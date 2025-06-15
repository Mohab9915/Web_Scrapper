"""
Matplotlib chart generator for RAG service.
This module handles generating charts using Matplotlib based on user queries and data.
"""
# Set Matplotlib backend before any other matplotlib imports
import matplotlib
# Force the Agg backend - must be done before importing pyplot
matplotlib.use('Agg', force=True)

import base64
import io
import json
import re
from typing import Dict, List, Any, Tuple

# Now import pyplot after backend is set
import matplotlib.pyplot as plt
import numpy as np


class MatplotlibChartGenerator:
    """
    A class to generate charts using Matplotlib based on user queries and data.
    """
    
    @staticmethod
    def extract_chart_params(query: str) -> Dict[str, Any]:
        """
        Extract chart parameters from the user query.
        
        Args:
            query (str): User query requesting a chart
            
        Returns:
            Dict[str, Any]: Dictionary containing chart parameters
        """
        query_lower = query.lower()
        
        # Extract chart type
        chart_type = "bar"  # Default chart type
        if "pie" in query_lower or "percentage" in query_lower or "proportion" in query_lower:
            chart_type = "pie"
        elif "line" in query_lower or "trend" in query_lower or "over time" in query_lower:
            chart_type = "line"
        elif "table" in query_lower:
            chart_type = "table"
        elif "stat" in query_lower:
            chart_type = "stats"
        else:
            pass
        # Extract top N
        top_n = None
        top_n_match = re.search(r"top\s+(\d+)", query_lower)
        if top_n_match:
            top_n = int(top_n_match.group(1))
            
        # Extract field to sort/filter by
        sort_field = None
        by_field_match = re.search(r"by\s+(\w+)", query_lower)
        if by_field_match:
            sort_field = by_field_match.group(1)
            
        params = {
            "chart_type": chart_type,
            "top_n": top_n,
            "sort_field": sort_field
        }
        return params
    
    @staticmethod
    def extract_data_from_context(context: str) -> List[Dict[str, Any]]:
        """
        Extract structured data from context.
        
        Args:
            context (str): The context text
            
        Returns:
            List[Dict[str, Any]]: List of data items
        """
        
        # Look for the JSON data marker in the context
        json_marker = "DATA (JSON):"
        data_items = []
        
        if json_marker in context:
            # Extract the JSON part
            json_part = context.split(json_marker, 1)[1].strip()
            
            # Try to parse the JSON data
            try:
                # Find the opening bracket of the JSON array
                if json_part.lstrip().startswith('['):
                    # Find matching closing bracket
                    bracket_count = 0
                    start_idx = json_part.find('[')
                    end_idx = -1
                    
                    for i, char in enumerate(json_part[start_idx:]):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_idx = start_idx + i + 1
                                break
                    
                    if end_idx > start_idx:
                        json_str = json_part[start_idx:end_idx]
                        parsed_data = json.loads(json_str)
                        if isinstance(parsed_data, list) and parsed_data:
                            data_items = parsed_data
            except json.JSONDecodeError as e:
                # Continue to fallback parsing methods
                pass
        
        # If no valid JSON data found or parsing failed, try to extract structured data
        if not data_items:
            
            # Try to find all JSON objects in the text
            try:
                # Look for patterns that might be JSON arrays
                json_patterns = [
                    r'\[\s*\{[^\[\]]*\}\s*(,\s*\{[^\[\]]*\}\s*)*\]',  # Standard JSON array
                    r'\[\s*\{[^\{\}]*\}\s*(,\s*\{[^\{\}]*\}\s*)*\]'   # Simplified pattern
                ]
                
                for pattern in json_patterns:
                    json_matches = re.findall(pattern, context, re.DOTALL)
                    if json_matches:
                        for match in json_matches:
                            full_match = match
                            if not match.startswith('['):
                                full_match = '[' + match
                            if not match.endswith(']'):
                                full_match = full_match + ']'
                            
                            try:
                                parsed_data = json.loads(full_match)
                                if isinstance(parsed_data, list) and parsed_data and isinstance(parsed_data[0], dict):
                                    data_items = parsed_data
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    if data_items:
                        break
            except Exception as e:
                pass
        # If still no data, try to parse line by line for structured data
        if not data_items:
            lines = context.split('\n')
            
            # Look for patterns in the text that might indicate structured data
            current_item = {}
            in_item = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for start of an item
                if line.startswith('{') or line.startswith('-') or line.startswith('*'):
                    if current_item and in_item:
                        # Clean the item data - remove quotes from keys and values
                        cleaned_item = {}
                        for k, v in current_item.items():
                            # Clean key
                            clean_key = k.strip('"').strip("'").strip(',').strip()
                            
                            # Clean and convert value
                            clean_val = v.strip('"').strip("'").strip(',').strip()
                            # Try to convert numeric values
                            try:
                                if '.' in clean_val:
                                    clean_val = float(clean_val)
                                else:
                                    clean_val = int(clean_val)
                            except ValueError:
                                pass  # Keep as string if conversion fails
                            
                            cleaned_item[clean_key] = clean_val
                        
                        data_items.append(cleaned_item)
                        current_item = {}
                    in_item = True
                
                # Check if this line contains a key-value pair
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        current_item[key] = value
                        in_item = True
            
            # Add the last item if it's not empty
            if current_item and in_item:
                # Clean the item data
                cleaned_item = {}
                for k, v in current_item.items():
                    clean_key = k.strip('"').strip("'").strip(',').strip()
                    clean_val = v.strip('"').strip("'").strip(',').strip()
                    try:
                        if '.' in clean_val:
                            clean_val = float(clean_val)
                        else:
                            clean_val = int(clean_val)
                    except ValueError:
                        pass
                    cleaned_item[clean_key] = clean_val
                
                data_items.append(cleaned_item)
        
        # Final data cleaning pass - ensure all items have consistent keys and data types
        if data_items:
            
            # Clean all items to ensure consistent structure
            cleaned_items = []
            for item in data_items:
                cleaned_item = {}
                for k, v in item.items():
                    # Clean key - remove quotes and extra characters
                    if isinstance(k, str):
                        clean_key = k.strip('"').strip("'").strip(',').strip()
                    else:
                        clean_key = str(k)
                    
                    # Clean value - convert strings to numbers where appropriate
                    if isinstance(v, str):
                        clean_val = v.strip('"').strip("'").strip(',').strip()
                        # Try to convert to number if it looks like one
                        try:
                            if '.' in clean_val:
                                clean_val = float(clean_val)
                            else:
                                clean_val = int(clean_val)
                        except ValueError:
                            pass  # Keep as string if conversion fails
                    else:
                        clean_val = v
                    
                    cleaned_item[clean_key] = clean_val
                
                cleaned_items.append(cleaned_item)
            
            data_items = cleaned_items
        
        return data_items
    
    @staticmethod
    def prepare_chart_data(data_items: List[Dict[str, Any]], params: Dict[str, Any]) -> Tuple[List[str], List[Any], str, str]:
        """
        Prepare data for chart generation based on extracted parameters.
        
        Args:
            data_items (List[Dict[str, Any]]): List of data items
            params (Dict[str, Any]): Chart parameters
            
        Returns:
            Tuple[List[str], List[Any], str, str]: labels, values, title, description
        """
        
        if not data_items:
            return [], [], "No Data Available", "No data could be extracted from the context."
        
        # Determine the field to use for values
        numeric_fields = []
        for item in data_items:
            for key, value in item.items():
                if isinstance(value, (int, float)) and key not in numeric_fields:
                    numeric_fields.append(key)
        
        
        # Use the specified sort field or find a suitable numeric field
        value_field = params.get("sort_field")
        if not value_field or value_field not in numeric_fields:
            # Try to find price-related fields first
            price_fields = [field for field in numeric_fields if any(price_term in field.lower() for price_term in ["price", "cost", "value", "amount"])]
            if price_fields:
                value_field = price_fields[0]
            elif numeric_fields:
                value_field = numeric_fields[0]
            else:
                # No numeric fields found, use the first field as label and assign default values
                first_key = list(data_items[0].keys())[0]
                labels = [str(item.get(first_key, "")) for item in data_items]
                values = list(range(1, len(data_items) + 1))
                title = f"Count of Items"
                description = f"Chart showing count of items"
                return labels, values, title, description
        else:
            pass
        # Determine label field (usually a non-numeric field)
        label_field = None
        for key in data_items[0].keys():
            if key != value_field and not isinstance(data_items[0].get(key), (int, float)):
                label_field = key
                break
        
        if not label_field:
            label_field = list(data_items[0].keys())[0]
        
        
        # Sort data if needed
        if value_field:
            data_items = sorted(data_items, key=lambda x: x.get(value_field, 0), reverse=True)
        
        # Apply top N filter if specified
        original_count = len(data_items)
        if params.get("top_n") and len(data_items) > params["top_n"]:
            data_items = data_items[:params["top_n"]]
        
        # Extract labels and values
        labels = [str(item.get(label_field, "")) for item in data_items]
        values = [item.get(value_field, 0) for item in data_items]
        
        
        # Generate title and description
        title_parts = []
        if params.get("chart_type") == "pie":
            title_parts.append("Distribution")
        else:
            if params.get("top_n"):
                title_parts.append(f"Top {params['top_n']}")
            title_parts.append("Items")
        
        if value_field:
            title_parts.append(f"by {value_field.title()}")
        
        title = " ".join(title_parts)
        
        if params.get("top_n"):
            description = f"Chart showing the top {params['top_n']} items by {value_field}"
        else:
            description = f"Chart showing items by {value_field}"
        
        
        return labels, values, title, description
    
    @staticmethod
    def generate_chart(labels: List[str], values: List[Any], params: Dict[str, Any], title: str) -> Tuple[str, str]:
        """
        Generate a chart using Matplotlib.
        
        Args:
            labels (List[str]): Labels for the chart
            values (List[Any]): Values for the chart
            params (Dict[str, Any]): Chart parameters
            title (str): Chart title
            
        Returns:
            Tuple[str, str]: Base64 encoded chart image and chart type
        """
        
        if not labels or not values:
            return "", "error"
        
        try:
            plt.figure(figsize=(10, 6))
            plt.title(title)
            
            chart_type = params.get("chart_type", "bar")
            
            # Generate colors for the chart
            num_colors = len(labels)
            colors = plt.cm.viridis(np.linspace(0, 1, num_colors))
            
            if chart_type == "pie":
                plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            elif chart_type == "line":
                plt.plot(labels, values)
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
            else:  # Default to bar chart
                plt.bar(labels, values, color=colors)
                plt.xticks(rotation=45)
                plt.grid(axis='y')
                plt.tight_layout()
            
            # Save the chart to a bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            # Convert the image to base64
            img_data = buf.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            plt.close()
            
            return img_base64, chart_type
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return "", "error"
