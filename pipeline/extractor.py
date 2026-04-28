import re
from turtle import position
from typing import List, Dict, Optional
from datetime import datetime
from unittest import result
#from unittest import result
#from pipeline.export.excel_exporter import export_to_excel
from cv2 import line
from shapely import buffer
from utils.excel_exporter import export_to_excel

from shapely import buffer


class Extractor:
    """Robust rule-based field extractor for invoice documents."""
    
    def __init__(self):
        # Define field patterns with variations
        self.field_patterns = {
            'invoice_number': [
                r'invoice\s*(?:no|number|#|num)?[\s:]*([A-Z0-9\-/]+)',
                r'inv\s*(?:no|number|#)?[\s:]*([A-Z0-9\-/]+)',
                r'bill\s*(?:no|number|#)?[\s:]*([A-Z0-9\-/]+)',
                r'(?:^|\|)\s*([A-Z0-9]{4,}\-[0-9]+)',
            ],
            'invoice_date': [
                r'invoice\s*date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'inv\s*date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'date\s*of\s*invoice[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'bill\s*date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'dated?[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            ],
            'due_date': [
                r'due\s*date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'payment\s*due[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'pay\s*by[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'due\s*on[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'payable\s*by[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            ],
            'total': [
                r'total[\s:]*[£$€]?\s*([\d,]+\.?\d{0,2})',
                r'amount\s*due[\s:]*[£$€]?\s*([\d,]+\.?\d{0,2})',
                r'grand\s*total[\s:]*[£$€]?\s*([\d,]+\.?\d{0,2})',
                r'balance\s*due[\s:]*[£$€]?\s*([\d,]+\.?\d{0,2})',
                r'total\s*amount[\s:]*[£$€]?\s*([\d,]+\.?\d{0,2})',
                r'net\s*total[\s:]*[£$€]?\s*([\d,]+\.?\d{0,2})',
            ]
        }
    
    def clean_text(self, text: str) -> str:
        """Clean OCR noise and normalize text."""
        if not text:
            return ""
        
        # Common OCR corrections
        ocr_fixes = {
            'lnvoice': 'Invoice',
            'Pertect': 'Perfect',
            'bes': 'Pipes',
            'Plumbling': 'Plumbing',
            'Emall': 'Email',
        }
        
        cleaned = text
        for wrong, right in ocr_fixes.items():
            cleaned = re.sub(wrong, right, cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """Convert amount string to float, handling various formats."""
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and commas
            clean_amount = re.sub(r'[£$€,\s]', '', amount_str)
            return float(clean_amount)
        except (ValueError, TypeError):
            return None
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date to DD/MM/YYYY format."""
        if not date_str:
            return None
        
        # Common date formats
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
            '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%m/%d/%Y', '%m-%d-%Y',
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%d/%m/%Y')
            except ValueError:
                continue
        
        return date_str  # Return as-is if can't parse
    
    def extract_field_from_lines(self, lines: List[str], patterns: List[str], 
                                  normalize_func=None) -> Optional[str]:
        """
        Extract a field using multiple regex patterns.
        Returns the first confident match.
        """
        best_match = None
        best_confidence = 0.0
        
        for line_idx, line in enumerate(lines):
            cleaned_line = self.clean_text(line)
            
            for pattern_idx, pattern in enumerate(patterns):
                match = re.search(pattern, cleaned_line, re.IGNORECASE)
                
                if match:
                    value = match.group(1).strip()
                    
                    # Calculate confidence
                    confidence = 1.0
                    
                    # Pattern priority (earlier patterns are more specific)
                    confidence -= pattern_idx * 0.1
                    
                    # Position bonus (earlier lines for header fields)
                    if line_idx < 5:
                        confidence += 0.2
                    
                    # Update best match if better confidence
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = value
        
        if best_match and normalize_func:
            return normalize_func(best_match)
        
        return best_match
    
    def extract_fields(self, lines_data: List) -> Dict[str, Optional[str]]:
        """
        Main extraction function.
        
        Args:
            lines_data: List of lines from LayoutParser (list of dicts with 'text' key)
                       OR list of strings
            
        Returns:
            Dictionary with extracted fields
        """
        # Convert to list of strings if needed
        if not lines_data:
            return {
                'invoice_number': None,
                'invoice_date': None,
                'due_date': None,
                'total': None
            }
        
        # Handle both formats: list of dicts OR list of strings
        if isinstance(lines_data[0], dict):
            # Convert list of line groups to text strings
            text_lines = []
            for line_group in lines_data:
                if isinstance(line_group, list):
                    # It's a list of items (from layout parser)
                    text = " | ".join([item.get('text', '') for item in line_group])
                    text_lines.append(text)
                else:
                    # It's already a dict with text
                    text_lines.append(line_group.get('text', ''))
        else:
            # Already strings
            text_lines = lines_data
        
        # Extract invoice number
        invoice_number = self.extract_field_from_lines(
            text_lines, 
            self.field_patterns['invoice_number']
        )
        if invoice_number:
            invoice_number = re.sub(r'[:|]+$', '', invoice_number.upper().strip())
        
        # Extract invoice date
        invoice_date = self.extract_field_from_lines(
            text_lines, 
            self.field_patterns['invoice_date'],
            self.normalize_date
        )
        
        # Extract due date
        due_date = self.extract_field_from_lines(
            text_lines, 
            self.field_patterns['due_date'],
            self.normalize_date
        )
        
        # Extract total
        total_str = self.extract_field_from_lines(
            text_lines, 
            self.field_patterns['total'] 

        )
        if not total_str:
            for line in reversed(text_lines):
                match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})', line)
                if match:
                    total_str = match.group()
                    break

        total_value = self.normalize_amount(total_str) if total_str else None

# find line where total came from
        total_line = None
        for i, line in enumerate(text_lines):
            if total_str and total_str in line:
                total_line = line
                total_pos = i
                break

        total = {
    "value": total_value,
    "confidence": self.compute_confidence(
        total_value,
        total_line,
        total_pos if total_line else 0,
        len(text_lines)
    )
}
        table = self.extract_table(text_lines)

        result = {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'total': total,
            'items': table
            }

        return result
    # if __name__ == "__main__":
    #     extractor = Extractor()
    
    #result = extractor.process("data/raw/invoice11.jpeg")  # your method name
    #extracted_data = extractor.extract_fields(lines_data)

    #export_to_excel(extracted_data)
    #from pipeline.export.excel_exporter import export_to_excel
    #export_to_excel(result, "data/output/invoice_output.xlsx")
    # def find_table_start(self, lines):
    #     for i, line in enumerate(lines):
    #         l = line.lower()
    #         if all(k in l for k in ["description", "quantity", "price"]):
    #             return i
    #     return -1
    def merge_multiline_rows(self, lines):
        merged = []
        buffer = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

        # If line starts lowercase or is continuation → merge
            if buffer and line[0].islower() :
                buffer += " " + line
            else:
                if buffer:
                    merged.append(buffer)
                buffer = line

        if buffer:
            merged.append(buffer)

        return merged

    def extract_table(self, lines):
        import re
        table = []
        start = -1

    # find header
        for i, line in enumerate(lines):
            l = line.lower()
            if "description" in l and ("amount" in l or "price" in l):
                start = i
                break
            if start == -1:
                for i, line in enumerate(lines):
                    if re.search(r'\d+\.\d{2}', line) and len(line.split()) > 3:
                        start = i - 1
                        break

        # if start == -1:
        #     return table
        print("TABLE START INDEX:", start)

    # process rows
        lines = self.merge_multiline_rows(lines)
        current_item = None
        for line in lines[start + 1:]:

            l = line.lower().strip()

        # stop at totals
            if any(k in l for k in ["subtotal", "amount due"]):
                break
            if "amount paid" in l:
                continue

# skip unwanted rows
            # if "vat" in l or "amount paid" in l:
            #     continue

            numbers = re.findall(r'-?\d+\.\d{2}', line)
            vat_match= re.search(r'(\d+%)', line)

            try:
                if "discount" in l:
                    amount = float(numbers[-1]) if numbers else 0.0
                    if current_item:
                        table.append(current_item)
                        current_item = None
                    table.append({
                        "description": "Discount",
                        "quantity": None,
                        "unit_price": None,
                        "vat": None,
                        "amount": -abs(amount)
                })
                elif len(numbers) >= 2:
                    if current_item:
                        table.append(current_item)
                    description = line

    # remove price values
                    description = re.sub(r'-?\d+\.\d{2}', '', description)

    # remove percentages (VAT like 20%)
                    description = re.sub(r'\d+%', '', description)

    # remove quantity patterns like "1 each", "2 qty", "3 x"
                    description = re.sub(r'\b\d+\s*(each|qty|x)?\b', '', description, flags=re.IGNORECASE)

    # clean extra spaces
                    description = re.sub(r'\s+', ' ', description).strip()
                    current_item = {
                    "description": description,
                    "quantity": 1,
                    "unit_price": float(numbers[-2]),
                    "vat": vat_match.group() if vat_match else None,
                    "amount": float(numbers[-1])
                }
                elif len(numbers) == 0:
                    if current_item:
                        current_item["description"] += " " + l

            except:
                continue
        if current_item:
            table.append(current_item)
        return table
    def compute_confidence(self, value, line, position, total_lines):
        import re

        score = 0

        if value:
            score += 0.4

        if line and any(k in line.lower() for k in ["total", "invoice", "date"]):
            score += 0.3

        if line and re.search(r'\d', line):
            score += 0.2

        if position > total_lines * 0.6:
            score += 0.1

        return round(min(score, 1.0), 2)
        

                    # table.append({
                    #      "description": description,
                    #      "quantity": 1,
                    #      "unit_price": float(numbers[0]),
                    #      "amount": float(numbers[-1])
                    # })  #mmmmmmm
            # append last item
    
    
    #clean_lines = list(dict.fromkeys(clean_lines))