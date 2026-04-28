class LayoutParser:
    def __init__(self):
        pass
    
    def group_by_lines(self, ocr_data, y_threshold=15):
        """
        Group OCR detections into lines based on Y-coordinate proximity.
        
        Args:
            ocr_data: List of dicts with 'bbox' and 'text' keys
            y_threshold: Maximum Y-distance to consider same line
            
        Returns:
            List of lines, where each line is a list of OCR items
        """
        def get_center(bbox):
            try:
                bbox = list(bbox)
                # polygon format (list of points)
                if isinstance(bbox[0], (list, tuple)):
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    return sum(ys)/len(ys), sum(xs)/len(xs)
                # flat format [x1, y1, x2, y2]
                return bbox[1], bbox[0]
            except:
                return 0, 0
        
        # Sort by Y (top to bottom)
        sorted_data = sorted(
            ocr_data,
            key=lambda x: get_center(x["bbox"])[0]
        )
        
        lines = []
        current_line = []
        last_y = None
        
        for item in sorted_data:
            y, x = get_center(item["bbox"])
            
            # Check if same line
            if last_y is None or abs(y - last_y) <= y_threshold:
                current_line.append((x, item))
            else:
                # Sort current line by X (left to right) and save
                current_line.sort(key=lambda z: z[0])
                lines.append([i[1] for i in current_line])
                
                # Start new line
                current_line = [(x, item)]
            
            last_y = y
        
        # Don't forget the last line
        if current_line:
            current_line.sort(key=lambda z: z[0])
            lines.append([i[1] for i in current_line])
        
        return lines
    
    def lines_to_text(self, lines, separator=" | "):
        """
        Convert grouped lines to text strings.
        
        Args:
            lines: Output from group_by_lines()
            separator: String to join words within a line
            
        Returns:
            List of text strings (one per line)
        """
        text_lines = []
        for line in lines:
            # Extract text from each item in the line
            words = [item.get('text', '') for item in line if item.get('text')]
            if words:
                text_lines.append(separator.join(words))
        return text_lines