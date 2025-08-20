import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from dateutil import parser
from dateutil.relativedelta import relativedelta


class DateExtractor:
    """Extracts and parses dates from natural language text."""
    
    def __init__(self):
        self.today = datetime.now()
        
        # Day name mappings
        self.days_of_week = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
            'fri': 4, 'sat': 5, 'sun': 6
        }
        
        # Month name mappings
        self.months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
            'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def extract_date(self, text: str) -> Optional[str]:
        """Extract date from natural language text and return in YYYY-MM-DD format."""
        text = text.lower().strip()
        
        # Try different extraction methods
        date_obj = (
            self._extract_relative_dates(text) or
            self._extract_specific_dates(text) or
            self._extract_day_names(text) or
            self._extract_formal_dates(text)
        )
        
        if date_obj:
            return date_obj.strftime('%Y-%m-%d')
        
        return None
    
    def _extract_relative_dates(self, text: str) -> Optional[datetime]:
        """Extract relative dates like 'tomorrow', 'next week', etc."""
        today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Today
        if any(word in text for word in ['today']):
            return today
        
        # Tomorrow
        if any(word in text for word in ['tomorrow']):
            return today + timedelta(days=1)
        
        # Yesterday
        if any(word in text for word in ['yesterday']):
            return today - timedelta(days=1)
        
        # Next week
        if 'next week' in text:
            return today + timedelta(days=7)
        
        # This week (assume Friday if not specific)
        if 'this week' in text:
            days_until_friday = (4 - today.weekday()) % 7
            return today + timedelta(days=days_until_friday)
        
        # Next month
        if 'next month' in text:
            return today + relativedelta(months=1)
        
        # In X days
        days_match = re.search(r'in (\d+) days?', text)
        if days_match:
            days = int(days_match.group(1))
            return today + timedelta(days=days)
        
        # In X weeks
        weeks_match = re.search(r'in (\d+) weeks?', text)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return today + timedelta(weeks=weeks)
        
        return None
    
    def _extract_day_names(self, text: str) -> Optional[datetime]:
        """Extract dates from day names like 'next monday', 'this friday'."""
        today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
        current_weekday = today.weekday()
        
        for day_name, day_num in self.days_of_week.items():
            # Next [day]
            if f'next {day_name}' in text:
                days_ahead = day_num - current_weekday
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            
            # This [day]
            elif f'this {day_name}' in text:
                days_ahead = day_num - current_weekday
                if days_ahead < 0:  # If the day has passed, assume next week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            
            # Just [day] (assume next occurrence)
            elif day_name in text and 'last' not in text:
                days_ahead = day_num - current_weekday
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
        return None
    
    def _extract_specific_dates(self, text: str) -> Optional[datetime]:
        """Extract specific dates like 'december 15', 'march 3rd', etc."""
        today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Month + Day patterns
        for month_name, month_num in self.months.items():
            # "december 15" or "dec 15"
            pattern = rf'{month_name}[\s]+(\d{{1,2}})(?:st|nd|rd|th)?'
            match = re.search(pattern, text)
            if match:
                day = int(match.group(1))
                try:
                    # Determine year (current year or next year if date has passed)
                    target_date = today.replace(month=month_num, day=day)
                    if target_date < today:
                        target_date = target_date.replace(year=today.year + 1)
                    return target_date
                except ValueError:
                    continue
            
            # "15th of december" or "15 of dec"
            pattern = rf'(\d{{1,2}})(?:st|nd|rd|th)?[\s]+of[\s]+{month_name}'
            match = re.search(pattern, text)
            if match:
                day = int(match.group(1))
                try:
                    target_date = today.replace(month=month_num, day=day)
                    if target_date < today:
                        target_date = target_date.replace(year=today.year + 1)
                    return target_date
                except ValueError:
                    continue
        
        return None
    
    def _extract_formal_dates(self, text: str) -> Optional[datetime]:
        """Extract formal date formats using dateutil parser."""
        # Common date patterns to try
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # MM/DD/YYYY or MM-DD-YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY/MM/DD or YYYY-MM-DD
            r'\d{1,2}[-/]\d{1,2}',             # MM/DD (current year)
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Try to parse the date
                    parsed_date = parser.parse(match, default=self.today)
                    
                    # If no year specified and date is in the past, assume next year
                    if parsed_date.year == self.today.year and parsed_date.date() < self.today.date():
                        if len(match.split('/')[-1]) <= 2 or len(match.split('-')[-1]) <= 2:
                            parsed_date = parsed_date.replace(year=self.today.year + 1)
                    
                    return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                except (ValueError, parser.ParserError):
                    continue
        
        return None
    
    def validate_date(self, date_str: str) -> Tuple[bool, Optional[str]]:
        """Validate if a date string is in correct YYYY-MM-DD format and is valid."""
        try:
            # Check format
            if not re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
                return False, "Date must be in YYYY-MM-DD format"
            
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Check if date is not in the past
            if date_obj.date() < self.today.date():
                return False, "Date cannot be in the past"
            
            # Check if date is not too far in the future (e.g., 2 years)
            max_date = self.today + relativedelta(years=2)
            if date_obj > max_date:
                return False, "Date cannot be more than 2 years in the future"
            
            return True, None
            
        except ValueError:
            return False, "Invalid date format"
    
    def get_date_suggestions(self, text: str) -> List[str]:
        """Get multiple date suggestions from text."""
        suggestions = []
        
        # Try to extract the main date
        main_date = self.extract_date(text)
        if main_date:
            suggestions.append(main_date)
        
        # Add some common alternatives if no date found
        if not main_date:
            today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
            suggestions.extend([
                (today + timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                (today + timedelta(days=7)).strftime('%Y-%m-%d'),  # Next week
                (today + timedelta(days=14)).strftime('%Y-%m-%d'), # Two weeks
            ])
        
        return suggestions