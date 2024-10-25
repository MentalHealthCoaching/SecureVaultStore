from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
import jwt
from datetime import datetime, timedelta
import os
import json

from secure_vault.core.database import get_db
from secure_vault.models.models import User, RecoveryQuestions, AuditLog
from secure_vault.core.crypto import CryptoSystem
from secure_vault.utils.password import PasswordValidator
from secure_vault.core.config import get_settings

class Language(str, Enum):
    DE = "de"
    EN = "en"
    ES = "es"

class RecoveryQuestion(BaseModel):
    id: int
    translations: Dict[str, str]

RECOVERY_QUESTIONS = [
    RecoveryQuestion(id=1, translations={
        "de": "Wie lautete der Name Ihres ersten Haustieres?",
        "en": "What was the name of your first pet?",
        "es": "¿Cuál fue el nombre de tu primera mascota?"
    }),
    RecoveryQuestion(id=2, translations={
        "de": "In welcher Stadt sind Sie geboren?",
        "en": "In which city were you born?",
        "es": "¿En qué ciudad naciste?"
    }),
    RecoveryQuestion(id=3, translations={
        "de": "Wie hieß Ihre erste Schule?",
        "en": "What was the name of your first school?",
        "es": "¿Cuál era el nombre de tu primera escuela?"
    }),
    RecoveryQuestion(id=4, translations={
        "de": "Wie hieß Ihr bester Freund in der Kindheit?",
        "en": "What was the name of your childhood best friend?",
        "es": "¿Cómo se llamaba tu mejor amigo de la infancia?"
    }),
    RecoveryQuestion(id=5, translations={
        "de": "Wie lautet der Mädchenname Ihrer Mutter?",
        "en": "What is your mother's maiden name?",
        "es": "¿Cuál es el apellido de soltera de tu madre?"
    }),
    RecoveryQuestion(id=6, translations={
        "de": "Welche Straße haben Sie als Kind bewohnt?",
        "en": "What street did you live on as a child?",
        "es": "¿En qué calle vivías cuando eras niño?"
    }),
    RecoveryQuestion(id=7, translations={
        "de": "Wie hieß Ihr erster Lehrer oder Ihre erste Lehrerin?",
        "en": "What was the name of your first teacher?",
        "es": "¿Cuál era el nombre de tu primer maestro o maestra?"
    }),
    RecoveryQuestion(id=8, translations={
        "de": "Wie hieß Ihr Lieblingsbuch als Kind?",
        "en": "What was your favorite book as a child?",
        "es": "¿Cuál era tu libro favorito de niño?"
    }),
    RecoveryQuestion(id=9, translations={
        "de": "Wie hieß Ihr erstes Auto?",
        "en": "What was the make of your first car?",
        "es": "¿Cuál era la marca de tu primer coche?"
    }),
    RecoveryQuestion(id=10, translations={
        "de": "Wie lautet der Name Ihres Lieblingslehrers?",
        "en": "What is the name of your favorite teacher?",
        "es": "¿Cuál es el nombre de tu maestro favorito?"
    }),
    RecoveryQuestion(id=11, translations={
        "de": "Wie hieß Ihr erstes Haustier?",
        "en": "What was the name of your first pet?",
        "es": "¿Cómo se llamaba tu primera mascota?"
    }),
    RecoveryQuestion(id=12, translations={
        "de": "In welchem Jahr haben Sie die Schule beendet?",
        "en": "In what year did you graduate from school?",
        "es": "¿En qué año te graduaste de la escuela?"
    }),
    RecoveryQuestion(id=13, translations={
        "de": "Wie lautet der Name Ihres Lieblingsfilms?",
        "en": "What is the name of your favorite movie?",
        "es": "¿Cuál es el nombre de tu película favorita?"
    }),
    RecoveryQuestion(id=14, translations={
        "de": "Wie lautet der Name Ihres ersten Chefs?",
        "en": "What was the name of your first boss?",
        "es": "¿Cuál era el nombre de tu primer jefe?"
    }),
    RecoveryQuestion(id=15, translations={
        "de": "Wie hieß Ihr erstes Fahrrad?",
        "en": "What was the brand of your first bicycle?",
        "es": "¿Cuál era la marca de tu primera bicicleta?"
    }),
    RecoveryQuestion(id=16, translations={
        "de": "In welcher Stadt haben Sie Ihren ersten Job gehabt?",
        "en": "In which city did you have your first job?",
        "es": "¿En qué ciudad tuviste tu primer trabajo?"
    }),
    RecoveryQuestion(id=17, translations={
        "de": "Was ist Ihr Lieblingsessen?",
        "en": "What is your favorite food?",
        "es": "¿Cuál es tu comida favorita?"
    }),
    RecoveryQuestion(id=18, translations={
        "de": "Wie lautet der Name Ihres ersten Freundes oder Ihrer ersten Freundin?",
        "en": "What was the name of your first boyfriend or girlfriend?",
        "es": "¿Cómo se llamaba tu primer novio o novia?"
    }),
    RecoveryQuestion(id=19, translations={
        "de": "Wie hieß Ihr erstes Haustier, das Sie selbst besaßen?",
        "en": "What was the name of the first pet you owned yourself?",
        "es": "¿Cómo se llamaba la primera mascota que poseíste tú mismo?"
    }),
    RecoveryQuestion(id=20, translations={
        "de": "Was war Ihr erstes Hobby?",
        "en": "What was your first hobby?",
        "es": "¿Cuál fue tu primer pasatiempo?"
    }),
    RecoveryQuestion(id=21, translations={
        "de": "In welchem Jahr haben Sie Ihren Führerschein gemacht?",
        "en": "In what year did you get your driver's license?",
        "es": "¿En qué año sacaste tu licencia de conducir?"
    }),
    RecoveryQuestion(id=22, translations={
        "de": "Wie hieß Ihr Lieblingslehrer in der Grundschule?",
        "en": "What was the name of your favorite elementary school teacher?",
        "es": "¿Cuál era el nombre de tu maestro favorito de primaria?"
    }),
    RecoveryQuestion(id=23, translations={
        "de": "Wie hieß der erste Film, den Sie im Kino gesehen haben?",
        "en": "What was the first movie you watched in a cinema?",
        "es": "¿Cuál fue la primera película que viste en el cine?"
    }),
    RecoveryQuestion(id=24, translations={
        "de": "Wie lautete der Name Ihres ersten besten Freundes?",
        "en": "What was the name of your first best friend?",
        "es": "¿Cuál era el nombre de tu primer mejor amigo?"
    }),
    RecoveryQuestion(id=25, translations={
        "de": "Welche Sportart haben Sie als Kind betrieben?",
        "en": "What sport did you play as a child?",
        "es": "¿Qué deporte practicabas de niño?"
    }),
    RecoveryQuestion(id=26, translations={
        "de": "Wie hieß Ihr erstes Haustier, das Sie als Erwachsener besessen haben?",
        "en": "What was the name of the first pet you owned as an adult?",
        "es": "¿Cómo se llamaba la primera mascota que poseíste como adulto?"
    }),
    RecoveryQuestion(id=27, translations={
        "de": "Was war Ihr Lieblingsfach in der Schule?",
        "en": "What was your favorite subject in school?",
        "es": "¿Cuál era tu asignatura favorita en la escuela?"
    }),
    RecoveryQuestion(id=28, translations={
        "de": "Wie hieß der erste Ort, an dem Sie im Urlaub waren?",
        "en": "What was the first place you went on vacation?",
        "es": "¿Cuál fue el primer lugar donde fuiste de vacaciones?"
    }),
    RecoveryQuestion(id=29, translations={
        "de": "Wie lautet der Name Ihres ersten Lehrers in der weiterführenden Schule?",
        "en": "What was the name of your first high school teacher?",
        "es": "¿Cuál era el nombre de tu primer maestro de secundaria?"
    }),
    RecoveryQuestion(id=30, translations={
        "de": "Was war Ihr Lieblingsspielzeug als Kind?",
        "en": "What was your favorite toy as a child?",
        "es": "¿Cuál era tu juguete favorito de niño?"
    }),
    RecoveryQuestion(id=31, translations={
        "de": "Wie hieß das erste Konzert, das Sie besucht haben?",
        "en": "What was the first concert you attended?",
        "es": "¿Cuál fue el primer concierto al que asististe?"
    }),
    RecoveryQuestion(id=32, translations={
        "de": "Wie hieß Ihr erstes Haustier?",
        "en": "What was the name of your first pet?",
        "es": "¿Cómo se llamaba tu primera mascota?"
    }),
    RecoveryQuestion(id=33, translations={
        "de": "Was ist Ihr Lieblingsurlaubsziel?",
        "en": "What is your favorite vacation destination?",
        "es": "¿Cuál es tu destino de vacaciones favorito?"
    }),
    RecoveryQuestion(id=34, translations={
        "de": "Welche ist Ihre Lieblingsfarbe?",
        "en": "What is your favorite color?",
        "es": "¿Cuál es tu color favorito?"
    }),
    RecoveryQuestion(id=35, translations={
        "de": "Wie hieß Ihr erster Lieblingsfilm als Kind?",
        "en": "What was the name of your first favorite movie as a child?",
        "es": "¿Cuál era el nombre de tu primera película favorita de niño?"
    }),
    RecoveryQuestion(id=36, translations={
        "de": "Was ist Ihr Lieblingssport?",
        "en": "What is your favorite sport?",
        "es": "¿Cuál es tu deporte favorito?"
    }),
    RecoveryQuestion(id=37, translations={
        "de": "Was ist Ihr Lieblingsessen aus Ihrer Kindheit?",
        "en": "What is your favorite childhood food?",
        "es": "¿Cuál es tu comida favorita de la infancia?"
    }),
    RecoveryQuestion(id=38, translations={
        "de": "Wie hieß Ihr erstes Haustier, das Sie als Kind besessen haben?",
        "en": "What was the name of the first pet you owned as a child?",
        "es": "¿Cómo se llamaba la primera mascota que poseíste como niño?"
    }),
    RecoveryQuestion(id=39, translations={
        "de": "Was war Ihr erster Beruf?",
        "en": "What was your first job?",
        "es": "¿Cuál fue tu primer trabajo?"
    }),
    RecoveryQuestion(id=40, translations={
        "de": "Wie lautet der Name Ihres ersten Partners?",
        "en": "What is the name of your first partner?",
        "es": "¿Cuál es el nombre de tu primer pareja?"
    }),
    RecoveryQuestion(id=41, translations={
        "de": "Wie hieß Ihre Grundschule?",
        "en": "What was the name of your elementary school?",
        "es": "¿Cómo se llamaba tu escuela primaria?"
    }),
    RecoveryQuestion(id=42, translations={
        "de": "Was war Ihr Lieblingsspiel auf dem Spielplatz?",
        "en": "What was your favorite playground activity?",
        "es": "¿Cuál era tu actividad favorita en el parque?"
    }),
    RecoveryQuestion(id=43, translations={
        "de": "Wie hieß Ihr erstes eigenes Haustier?",
        "en": "What was the name of your first own pet?",
        "es": "¿Cómo se llamaba tu primera mascota propia?"
    }),
    RecoveryQuestion(id=44, translations={
        "de": "Was war Ihr erstes Musikinstrument?",
        "en": "What was your first musical instrument?",
        "es": "¿Cuál fue tu primer instrumento musical?"
    }),
    RecoveryQuestion(id=45, translations={
        "de": "Wie hieß Ihr erstes Urlaubsland?",
        "en": "What was the first country you visited on vacation?",
        "es": "¿Cuál fue el primer país que visitaste de vacaciones?"
    }),
    RecoveryQuestion(id=46, translations={
        "de": "Wie lautet der Name Ihrer ersten Schule?",
        "en": "What is the name of your first school?",
        "es": "¿Cuál es el nombre de tu primera escuela?"
    }),
    RecoveryQuestion(id=47, translations={
        "de": "Was war das erste Spielzeug, das Sie besaßen?",
        "en": "What was the first toy you owned?",
        "es": "¿Cuál fue el primer juguete que poseíste?"
    }),
    RecoveryQuestion(id=48, translations={
        "de": "Was war Ihr Lieblingsessen in der Schule?",
        "en": "What was your favorite school lunch?",
        "es": "¿Cuál era tu comida favorita en la escuela?"
    }),
    RecoveryQuestion(id=49, translations={
        "de": "Wie hieß Ihr Lieblingsspiel auf dem Pausenhof?",
        "en": "What was your favorite game in the schoolyard?",
        "es": "¿Cuál era tu juego favorito en el patio de la escuela?"
    }),
    RecoveryQuestion(id=50, translations={
        "de": "Was war das erste Buch, das Sie gelesen haben?",
        "en": "What was the first book you read?",
        "es": "¿Cuál fue el primer libro que leíste?"
    })
]

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()
crypto = CryptoSystem()
password_validator = PasswordValidator(settings)

class RecoverySystem:
    def __init__(self, crypto: CryptoSystem, db: AsyncSession):
        self.crypto = crypto
        self.db = db
        self.min_questions = 5
        self.required_correct_answers = 4

    def get_available_questions(self, lang: Language) -> List[Dict]:
        """Gibt alle verfügbaren Fragen in der gewählten Sprache zurück"""
        return [
            {
                "id": q.id,
                "question": q.translations[lang]
            }
            for q in RECOVERY_QUESTIONS
        ]

    async def setup_questions(
        self,
        user: User,
        question_answers: List[Dict[str, str]]  # [{"question_id": int, "answer": str}]
    ):
        """Speichert die Recovery-Fragen und Antworten"""
        if len(question_answers) < self.min_questions:
            raise ValueError(f"At least {self.min_questions} questions required")

        # Lösche alte Fragen falls vorhanden
        await self.db.execute(
            delete(RecoveryQuestions).where(RecoveryQuestions.user_id == user.user_id)
        )

        # Kombiniere alle Antworten für den Recovery-Key
        answers = [qa["answer"] for qa in question_answers]
        recovery_key = self.crypto.derive_key_from_answers(answers)

        # Hole und verschlüssele Master-Key
        master_key = self.crypto.decrypt_master_key(
            user.master_key_encrypted,
            user.current_password_key
        )
        encrypted_master_key = self.crypto.encrypt_master_key(
            master_key,
            recovery_key
        )

        # Speichere Fragen und verschlüsselten Master-Key
        for qa in question_answers:
            question = RecoveryQuestions(
                user_id=user.user_id,
                question_id=qa["question_id"],
                answer_hash=self.crypto.hash_answer(qa["answer"])
            )
            self.db.add(question)

        user.recovery_key_encrypted = encrypted_master_key
        user.has_recovery = True
        await self.db.commit()

    async def get_user_questions(
        self,
        user_id: str,
        lang: Language
    ) -> List[str]:
        """Holt die Fragen eines Users in der gewünschten Sprache"""
        questions = await self.db.execute(
            select(RecoveryQuestions)
            .where(RecoveryQuestions.user_id == user_id)
        )
        questions = questions.scalars().all()

        return [
            RECOVERY_QUESTIONS[q.question_id].translations[lang]
            for q in questions
        ]

    async def verify_answers(
        self,
        user_id: str,
        answers: List[str]
    ) -> Tuple[bool, Optional[bytes]]:
        """Verifiziert die Antworten und gibt den Master-Key zurück"""
        questions = await self.db.execute(
            select(RecoveryQuestions)
            .where(RecoveryQuestions.user_id == user_id)
            .order_by(RecoveryQuestions.question_id)
        )
        questions = questions.scalars().all()

        if not questions:
            return False, None

        correct_answers = 0
        for q, answer in zip(questions, answers):
            if self.crypto.verify_answer(answer, q.answer_hash):
                correct_answers += 1

        if correct_answers < self.required_correct_answers:
            return False, None

        recovery_key = self.crypto.derive_key_from_answers(answers)
        
        user = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        try:
            master_key = self.crypto.decrypt_master_key(
                user.recovery_key_encrypted,
                recovery_key
            )
            return True, master_key
        except:
            return False, None

@router.post("/auth")
async def authenticate(
    user_id: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()
        
        is_new_user = False
        needs_recovery_setup = False

        if not user:
            is_valid, message = password_validator.validate(password)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=message
                )
            
            keys = crypto.generate_user_keys(password)
            user = User(
                user_id=user_id,
                password_hash=crypto.hash_password(password),
                master_key_encrypted=keys['master_key_encrypted'],
                public_key=keys['public_key'],
                has_recovery=False,
                created_at=datetime.utcnow()
            )
            db.add(user)
            is_new_user = True
            needs_recovery_setup = True
        else:
            if not crypto.verify_password(password, user.password_hash):
                log = AuditLog(
                    user_id=user_id,
                    action="failed_login",
                    success=False
                )
                db.add(log)
                await db.commit()
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )

            needs_recovery_setup = not user.has_recovery

        user.last_login = datetime.utcnow()
        access_token = crypto.create_access_token(user.user_id)
        
        log = AuditLog(
            user_id=user_id,
            action="login",
            success=True,
            details="new_user" if is_new_user else "existing_user"
        )
        db.add(log)
        
        await db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "new_user": is_new_user,
            "needs_recovery_setup": needs_recovery_setup
        }

    except Exception as e:
        await db.rollback()
        raise

@router.get("/auth/recovery-questions")
async def get_recovery_questions(
    lang: Language = Language.EN
):
    """Gibt alle verfügbaren Recovery-Fragen zurück"""
    recovery_system = RecoverySystem(crypto, None)
    return {
        "questions": recovery_system.get_available_questions(lang)
    }

@router.post("/auth/setup-recovery")
async def setup_recovery(
    question_answers: List[Dict[str, str]],  # [{"question_id": int, "answer": str}]
    current_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Richtet Recovery-Fragen für einen Benutzer ein"""
    try:
        if not crypto.verify_password(current_password, current_user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid password"
            )
            
        recovery_system = RecoverySystem(crypto, db)
        await recovery_system.setup_questions(current_user, question_answers)
        
        log = AuditLog(
            user_id=current_user.user_id,
            action="setup_recovery",
            success=True
        )
        db.add(log)
        await db.commit()
        
        return {
            "message": "Recovery questions successfully set up"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except Exception as e:
        await db.rollback()
        raise

@router.get("/auth/recovery/{user_id}/questions")
async def get_user_recovery_questions(
    user_id: str,
    lang: Language = Language.EN,
    db: AsyncSession = Depends(get_db)
):
    """Gibt die Recovery-Fragen eines Users zurück"""
    recovery_system = RecoverySystem(crypto, db)
    
    user = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = user.scalar_one_or_none()
    
    if not user or not user.has_recovery:
        raise HTTPException(
            status_code=404,
            detail="No recovery questions found"
        )
        
    questions = await recovery_system.get_user_questions(user_id, lang)
    
    return {
        "questions": questions
    }

@router.post("/auth/recovery/{user_id}/verify")
async def verify_recovery_answers(
    user_id: str,
    answers: List[str],
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """Verifiziert Recovery-Antworten und setzt neues Passwort"""
    try:
        is_valid, message = password_validator.validate(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=message
            )
            
        recovery_system = RecoverySystem(crypto, db)
        success, master_key = await recovery_system.verify_answers(user_id, answers)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid recovery answers"
            )
            
        user = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
            
        # Verschlüssele bestehenden Master-Key mit neuem Passwort
        new_master_key_encrypted = crypto.encrypt_master_key(
            master_key,
            new_password
        )
        
        # Update user
        user.password_hash = crypto.hash_password(new_password)
        user.master_key_encrypted = new_master_key_encrypted
        user.password_changed_at = datetime.utcnow()
        
        log = AuditLog(
            user_id=user_id,
            action="recovery_password_reset",
            success=True
        )
        db.add(log)
        
        await db.commit()
        
        return {
            "message": "Password successfully reset. All documents remain accessible."
        }
        
    except Exception as e:
        await db.rollback()
        raise

@router.post("/auth/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ändert das Passwort eines Benutzers"""
    try:
        is_valid, message = password_validator.validate(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=message
            )
            
        if not crypto.verify_password(old_password, current_user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid current password"
            )
            
        # Entschlüssele Master-Key mit altem Passwort
        master_key = crypto.decrypt_master_key(
            current_user.master_key_encrypted,
            old_password
        )
        
        # Verschlüssele mit neuem Passwort
        new_master_key_encrypted = crypto.encrypt_master_key(
            master_key,
            new_password
        )
        
        # Update user
        current_user.password_hash = crypto.hash_password(new_password)
        current_user.master_key_encrypted = new_master_key_encrypted
        current_user.password_changed_at = datetime.utcnow()
        
        log = AuditLog(
            user_id=current_user.user_id,
            action="change_password",
            success=True
        )
        db.add(log)
        
        await db.commit()
        
        return {
            "message": "Password successfully changed"
        }
        
    except Exception as e:
        await db.rollback()
        raise