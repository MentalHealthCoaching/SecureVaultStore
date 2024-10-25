from typing import Tuple
import re
from zxcvbn import zxcvbn  # Entropy-basierte Passwort-Stärke-Bewertung

class PasswordValidator:
    def __init__(self, config):
        self.config = config
        # Reasonable defaults, können via config.ini überschrieben werden
        self.min_length = config.get('min_password_length', 12)
        self.max_length = config.get('max_password_length', 64)
        self.min_strength_score = config.get('min_password_strength', 3)  # zxcvbn score 0-4
        
    def validate(self, password: str) -> Tuple[bool, str]:
        """
        Validiert ein Passwort und gibt (valid, message) zurück.
        Verwendet zxcvbn für intelligente Stärkeanalyse.
        """
        # Basis-Checks
        if len(password) < self.min_length:
            return False, f"Password must be at least {self.min_length} characters long"
            
        if len(password) > self.max_length:
            return False, f"Password cannot be longer than {self.max_length} characters"
            
        # Check auf einfache Muster
        if password.isdigit():
            return False, "Password cannot contain only numbers"
            
        if password.isalpha():
            return False, "Password must contain at least one number"
            
        if password.islower() or password.isupper():
            return False, "Password must contain mixed case letters"
            
        # Intelligente Stärkeanalyse mit zxcvbn
        result = zxcvbn(password)
        
        if result['score'] < self.min_strength_score:
            suggestions = result['feedback']['suggestions']
            warning = result['feedback']['warning']
            return False, f"Password too weak: {warning}. Suggestions: {', '.join(suggestions)}"
            
        # Spezielle Checks für zu komplexe Passwörter
        if self._is_too_complex(password):
            return False, "Password is too complex for practical use. Please simplify."
            
        return True, "Password meets requirements"
        
    def _is_too_complex(self, password: str) -> bool:
        """
        Prüft ob ein Passwort zu komplex für praktische Nutzung ist.
        """
        # Zähle verschiedene Zeichenarten
        char_types = 0
        if re.search(r'[a-z]', password): char_types += 1
        if re.search(r'[A-Z]', password): char_types += 1
        if re.search(r'[0-9]', password): char_types += 1
        if re.search(r'[^a-zA-Z0-9]', password): char_types += 1
        
        # Zu viele verschiedene Sonderzeichen
        special_chars = len(set(re.findall(r'[^a-zA-Z0-9]', password)))
        if special_chars > 3:
            return True
            
        # Zu viele Zeichenwechsel
        transitions = 0
        last_type = None
        for c in password:
            current_type = None
            if c.islower(): current_type = 'lower'
            elif c.isupper(): current_type = 'upper'
            elif c.isdigit(): current_type = 'digit'
            else: current_type = 'special'
            
            if last_type and current_type != last_type:
                transitions += 1
            last_type = current_type
            
        if transitions > len(password) * 0.7:  # Zu viele Wechsel
            return True
            
        return False

    def generate_feedback(self, password: str) -> dict:
        """
        Generiert hilfreiches Feedback zur Passwortstärke.
        """
        result = zxcvbn(password)
        
        return {
            'score': result['score'],  # 0-4
            'estimated_guesses': result['guesses'],
            'crack_time': result['crack_times_display']['offline_fast_hashing_1e10_per_second'],
            'warning': result['feedback']['warning'],
            'suggestions': result['feedback']['suggestions'],
            'is_complex_enough': result['score'] >= self.min_strength_score,
            'is_too_complex': self._is_too_complex(password)
        }

    def get_requirements(self) -> str:
        """
        Gibt eine benutzerfreundliche Beschreibung der Anforderungen zurück.
        """
        return f"""Password requirements:
- Length: {self.min_length}-{self.max_length} characters
- Must contain:
  * Lower and uppercase letters
  * At least one number
  * At least one special character
- Should be:
  * Easy to remember but hard to guess
  * Not too complex for practical use
  * Not based on personal information
  * Not a common password pattern

Good examples:
✅ "Correct-Horse-Battery-Staple"
✅ "ILike2EatPizza!"
✅ "My1stApartmentWas@123"

Bad examples:
❌ "Password123!" (too common)
❌ "aaaaAAA111!!!" (pattern too simple)
❌ "P@s$w0rd" (too common with substitutions)
❌ "Kj#9$mP2&5@qR" (too complex to remember)
"""
