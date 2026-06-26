import json
import logging
import random

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.quiz import ExamSession, QuizQuestion, UserAnswer
from backend.security import limiter, get_current_user

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])
logger = logging.getLogger(__name__)

LEVEL_ORDER = ["Junior Otaku", "Senior Otaku", "Master Otaku", "Otaku Legendaire"]

class QuestionOut(BaseModel):
    id: int
    question: str
    options: List[str]
    difficulty: str
    category: Optional[str] = None

class StartResponse(BaseModel):
    session_id: int
    questions: List[QuestionOut]
    level: str

class SubmitRequest(BaseModel):
    session_id: int
    answers: List[int] = Field(..., min_length=10, max_length=20)

class SubmitResponse(BaseModel):
    score: int
    level: str
    total: int
    correct: int
    details: List[dict]

class CongratulateRequest(BaseModel):
    username: str
    level: str
    score: int

class ProgressOut(BaseModel):
    highest_unlocked: str
    completed_levels: List[str]

_ALL_QUESTIONS = [
  {
    "question": "Dans Naruto, quel est le nom du démon scellé en Naruto ?",
    "options": [
      "Kurama",
      "Shukaku",
      "Matatabi",
      "Saiken"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans One Piece, comment s'appelle le bateau de Luffy ?",
    "options": [
      "Thousand Sunny",
      "Moby Dick",
      "Oro Jackson",
      "Red Force"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du personnage principal de Death Note ?",
    "options": [
      "L",
      "Light Yagami",
      "Near",
      "Mello"
    ],
    "correct_index": 1,
    "category": "Death Note",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Dragon Ball Z, quel est le nom du frère de Goku ?",
    "options": [
      "Raditz",
      "Tarble",
      "Bardock",
      "Turles"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel animé présente un garçon qui cherche à devenir le plus grand épéiste ?",
    "options": [
      "One Piece",
      "Bleach",
      "Naruto",
      "Hunter x Hunter"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Demon Slayer, comment s'appelle la sœur de Tanjiro ?",
    "options": [
      "Nezuko",
      "Kanao",
      "Shinobu",
      "Mitsuri"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste d'Attack on Titan ?",
    "options": [
      "Eren Yeager",
      "Levi Ackerman",
      "Mikasa Ackerman",
      "Armin Arlelt"
    ],
    "correct_index": 0,
    "category": "Attack on Titan",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Fullmetal Alchemist, quel est le surnom d'Edward Elric ?",
    "options": [
      "Fullmetal Alchemist",
      "Flame Alchemist",
      "Thunder Alchemist",
      "Slash Alchemist"
    ],
    "correct_index": 0,
    "category": "Fullmetal Alchemist",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du chat-robot dans Doraemon ?",
    "options": [
      "Doraemon",
      "Nobita",
      "Shizuka",
      "Gian"
    ],
    "correct_index": 0,
    "category": "Doraemon",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Pokemon, quel est le pokemon de départ de type plante de Kanto ?",
    "options": [
      "Bulbizarre",
      "Salamèche",
      "Carapuce",
      "Pikachu"
    ],
    "correct_index": 0,
    "category": "Pokemon",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du héros masqué dans My Hero Academia ?",
    "options": [
      "All Might",
      "Deku",
      "Bakugo",
      "Shoto"
    ],
    "correct_index": 1,
    "category": "My Hero Academia",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Sword Art Online, quel est le pseudo du protagoniste ?",
    "options": [
      "Kirito",
      "Asuna",
      "Klein",
      "Agil"
    ],
    "correct_index": 0,
    "category": "Sword Art Online",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du magicien dans Fairy Tail ?",
    "options": [
      "Natsu",
      "Gray",
      "Erza",
      "Lucy"
    ],
    "correct_index": 0,
    "category": "Fairy Tail",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Hunter x Hunter, quel est le nom du protagoniste ?",
    "options": [
      "Gon",
      "Killua",
      "Kurapika",
      "Leorio"
    ],
    "correct_index": 0,
    "category": "Hunter x Hunter",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du personnage principal de Cowboy Bebop ?",
    "options": [
      "Spike Spiegel",
      "Jet Black",
      "Vicious",
      "Faye Valentine"
    ],
    "correct_index": 0,
    "category": "Cowboy Bebop",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Tokyo Ghoul, quel est le nom du protagoniste ?",
    "options": [
      "Ken Kaneki",
      "Hide",
      "Touka",
      "Ayato"
    ],
    "correct_index": 0,
    "category": "Tokyo Ghoul",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du manga sur les exorcistes utilisant des armes spirituelles ?",
    "options": [
      "Blue Exorcist",
      "D.Gray-man",
      "Jujutsu Kaisen",
      "Seraph of the End"
    ],
    "correct_index": 2,
    "category": "Jujutsu Kaisen",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans JoJo's Bizarre Adventure, quel est le nom du personnage principal de la partie 3 ?",
    "options": [
      "Jotaro Kujo",
      "Joseph Joestar",
      "Dio Brando",
      "Jonathan Joestar"
    ],
    "correct_index": 0,
    "category": "JoJo",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du héros chauve dans One Punch Man ?",
    "options": [
      "Saitama",
      "Genos",
      "King",
      "Mumen Rider"
    ],
    "correct_index": 0,
    "category": "One Punch Man",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Steins;Gate, quel est le nom du protagoniste ?",
    "options": [
      "Rintaro Okabe",
      "Mayuri Shiina",
      "Kurisu Makise",
      "Daru Hashida"
    ],
    "correct_index": 0,
    "category": "Steins;Gate",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du démon dans Demon Slayer ?",
    "options": [
      "Muzan Kibutsuji",
      "Tanjuro",
      "Yoriichi",
      "Kokushibo"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Naruto, quel est le nom de l'équipe de Kakashi ?",
    "options": [
      "Team 7",
      "Team 8",
      "Team 9",
      "Team 10"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom de l'école dans My Hero Academia ?",
    "options": [
      "U.A. High School",
      "Shiketsu High School",
      "Ketsubutsu Academy",
      "Isamu Academy"
    ],
    "correct_index": 0,
    "category": "My Hero Academia",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans One Piece, quel est le nom du premier ami de Luffy ?",
    "options": [
      "Zoro",
      "Nami",
      "Usopp",
      "Sanji"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du personnage principal de Bleach ?",
    "options": [
      "Ichigo Kurosaki",
      "Rukia Kuchiki",
      "Renji Abarai",
      "Byakuya Kuchiki"
    ],
    "correct_index": 0,
    "category": "Bleach",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Dragon Ball, quel est le nom de la première transformation de Goku ?",
    "options": [
      "Super Saiyan",
      "Super Saiyan 2",
      "Super Saiyan 3",
      "Super Saiyan God"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du village de Naruto ?",
    "options": [
      "Konoha",
      "Suna",
      "Kiri",
      "Iwa"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Demon Slayer, quel élément Tanjiro utilise-t-il ?",
    "options": [
      "Eau",
      "Feu",
      "Vent",
      "Tonnerre"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le nom du vaisseau spatial dans Cowboy Bebop ?",
    "options": [
      "Bebop",
      "Swordfish",
      "Redtail",
      "Hammer"
    ],
    "correct_index": 0,
    "category": "Cowboy Bebop",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Dans Attack on Titan, quel est le nom du titan d'Eren ?",
    "options": [
      "Titan Assaillant",
      "Titan Colossal",
      "Titan Cuirassé",
      "Titan Bestial"
    ],
    "correct_index": 0,
    "category": "Attack on Titan",
    "difficulty": "Junior Otaku"
  },
  {
    "question": "Quel est le vrai nom de Goku ?",
    "options": [
      "Kakarot",
      "Bardock",
      "Raditz",
      "Kakarotto"
    ],
    "correct_index": 0,
    "difficulty": "Junior Otaku",
    "category": "Dragon Ball"
  },
  {
    "question": "Dans One Piece, quel est le rêve de Luffy ?",
    "options": [
      "Devenir Hokage",
      "Trouver le One Piece et devenir Roi des Pirates",
      "Devenir l'épéiste le plus fort",
      "Dessiner le meilleur manga"
    ],
    "correct_index": 1,
    "difficulty": "Junior Otaku",
    "category": "One Piece"
  },
  {
    "question": "Quel est le nom du démon-épéiste dans Demon Slayer ?",
    "options": [
      "Tanjiro",
      "Zenitsu",
      "Inosuke",
      "Giyu"
    ],
    "correct_index": 0,
    "difficulty": "Junior Otaku",
    "category": "Demon Slayer"
  },
  {
    "question": "Quel animé met en scène un garçon qui contrôle les titans ?",
    "options": [
      "Tokyo Ghoul",
      "Attack on Titan",
      "Seraph of the End",
      "Parasyte"
    ],
    "correct_index": 1,
    "difficulty": "Junior Otaku",
    "category": "Attack on Titan"
  },
  {
    "question": "Dans Death Note, quel est le vrai nom de Kira ?",
    "options": [
      "L",
      "Near",
      "Light Yagami",
      "Mello"
    ],
    "correct_index": 2,
    "difficulty": "Junior Otaku",
    "category": "Death Note"
  },
  {
    "question": "Dans Naruto Shippuden, quel est le vrai nom de l'Akatsuki ?",
    "options": [
      "Organisation Akatsuki",
      "Groupe des 9",
      "Order of the Dawn",
      "L'Aube Rouge"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du père de Luffy ?",
    "options": [
      "Monkey D. Dragon",
      "Gold D. Roger",
      "Sengoku",
      "Garp"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Death Note, quel est le nom du détective L ?",
    "options": [
      "L Lawliet",
      "Nate River",
      "Mihael Keehl",
      "Quillsh Wammy"
    ],
    "correct_index": 0,
    "category": "Death Note",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du premier Super Saiyan de l'histoire ?",
    "options": [
      "Yamoshi",
      "Bardock",
      "Goku",
      "Vegeta"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Demon Slayer, quel est le niveau le plus élevé des pourfendeurs ?",
    "options": [
      "Hashira",
      "Kinoe",
      "Kototo",
      "Hinoe"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du père d'Edward Elric ?",
    "options": [
      "Van Hohenheim",
      "Roy Mustang",
      "Scar",
      "King Bradley"
    ],
    "correct_index": 0,
    "category": "Fullmetal Alchemist",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Bleach, quel est le nom de l'épée de Rukia ?",
    "options": [
      "Sode no Shirayuki",
      "Zangetsu",
      "Hyorinmaru",
      "Senbonzakura"
    ],
    "correct_index": 0,
    "category": "Bleach",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du dieu de la mort dans Death Note ?",
    "options": [
      "Ryuk",
      "Rem",
      "Sidoh",
      "Gelus"
    ],
    "correct_index": 0,
    "category": "Death Note",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans One Piece, quel est le nom de l'épéiste qui manie trois sabres ?",
    "options": [
      "Roronoa Zoro",
      "Brook",
      "Cavendish",
      "Killer"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du village de Leaf ?",
    "options": [
      "Konohagakure",
      "Sunagakure",
      "Kirigakure",
      "Kumogakure"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Attack on Titan, quel est le nom de la compagne d'Eren ?",
    "options": [
      "Mikasa Ackerman",
      "Historia Reiss",
      "Annie Leonhart",
      "Sasha Blouse"
    ],
    "correct_index": 0,
    "category": "Attack on Titan",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du père adoptif de Naruto ?",
    "options": [
      "Iruka Umino",
      "Kakashi Hatake",
      "Jiraiya",
      "Tsunade"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Dragon Ball, quel est le nom de la planète de Vegeta ?",
    "options": [
      "Planète Vegeta",
      "Namek",
      "Earth",
      "Yardrat"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du groupe de mercenaires dans Jujutsu Kaisen ?",
    "options": [
      "Les masques de fer",
      "Geto's group",
      "Les sorciers errants",
      "Q"
    ],
    "correct_index": 1,
    "category": "Jujutsu Kaisen",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans JoJo's Bizarre Adventure, quel est le nom du stand de Dio ?",
    "options": [
      "The World",
      "Star Platinum",
      "King Crimson",
      "Gold Experience"
    ],
    "correct_index": 0,
    "category": "JoJo",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom de l'arme de Killua dans Hunter x Hunter ?",
    "options": [
      "Eleclerc",
      "Godspeed",
      "Thunderbolt",
      "Lightning Palm"
    ],
    "correct_index": 0,
    "category": "Hunter x Hunter",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Steins;Gate, comment s'appelle le four micro-onde ?",
    "options": [
      "Telephone Microwave (Tento)",
      "SERN Device",
      "IBM 5100",
      "Laboratory Machine"
    ],
    "correct_index": 0,
    "category": "Steins;Gate",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom de la technique ultime d'All Might ?",
    "options": [
      "United States of Smash",
      "Detroit Smash",
      "Texas Smash",
      "Carolina Smash"
    ],
    "correct_index": 0,
    "category": "My Hero Academia",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Fairy Tail, quel est le nom du dragon de Natsu ?",
    "options": [
      "Igneel",
      "Grandine",
      "Metalicana",
      "Zilconis"
    ],
    "correct_index": 0,
    "category": "Fairy Tail",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste de Code Geass ?",
    "options": [
      "Lelouch Lamperouge",
      "Suzaku Kururugi",
      "C.C.",
      "Kallen Stadtfeld"
    ],
    "correct_index": 0,
    "category": "Code Geass",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans One Punch Man, quel est le rang de Saitama ?",
    "options": [
      "Classe C",
      "Classe B",
      "Classe S",
      "Classe A"
    ],
    "correct_index": 0,
    "category": "One Punch Man",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du groupe de musique dans Beck ?",
    "options": [
      "Beck",
      "The Dying Breed",
      "The Choke",
      "The Moon"
    ],
    "correct_index": 0,
    "category": "Beck",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Evangelion, quel est le nom de l'organisation ?",
    "options": [
      "NERV",
      "SEELE",
      "WILLE",
      "UN Forces"
    ],
    "correct_index": 0,
    "category": "Evangelion",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du héros principal de Samurai Champloo ?",
    "options": [
      "Mugen",
      "Jin",
      "Fuu",
      "Kariya"
    ],
    "correct_index": 0,
    "category": "Samurai Champloo",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Trigun, quel est le nom du protagoniste ?",
    "options": [
      "Vash the Stampede",
      "Knives Millions",
      "Wolfwood",
      "Meryl"
    ],
    "correct_index": 0,
    "category": "Trigun",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du personnage principal d'Inuyasha ?",
    "options": [
      "Inuyasha",
      "Kagome",
      "Sesshomaru",
      "Kikyo"
    ],
    "correct_index": 0,
    "category": "Inuyasha",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Ranma 1/2, quel est le nom du protagoniste ?",
    "options": [
      "Ranma",
      "Akane",
      "Ryoga",
      "Shampoo"
    ],
    "correct_index": 0,
    "category": "Ranma 1/2",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du monstre dans Parasyte ?",
    "options": [
      "Parasyte",
      "Miguel",
      "Shinichi",
      "Goto"
    ],
    "correct_index": 0,
    "category": "Parasyte",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Gintama, quel est le nom du protagoniste ?",
    "options": [
      "Gintoki Sakata",
      "Shinpachi Shimura",
      "Kagura",
      "Hijikata"
    ],
    "correct_index": 0,
    "category": "Gintama",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste d'Initial D ?",
    "options": [
      "Takumi Fujiwara",
      "Keisuke Takahashi",
      "Itsuki Takeuchi",
      "Kyoichi Sudo"
    ],
    "correct_index": 0,
    "category": "Initial D",
    "difficulty": "Senior Otaku"
  },
  {
    "question": "Dans Naruto, quel Sharingan évolue en Rinnegan ?",
    "options": [
      "Sharingan de Sasuke",
      "Sharingan d'Itachi",
      "Sharingan de Madara",
      "Sharingan de Kakashi"
    ],
    "correct_index": 2,
    "difficulty": "Senior Otaku",
    "category": "Naruto"
  },
  {
    "question": "Qui est le capitaine de la 5e division dans Bleach ?",
    "options": [
      "Shinji Hirako",
      "Sosuke Aizen",
      "Byakuya Kuchiki",
      "Toshiro Hitsugaya"
    ],
    "correct_index": 1,
    "difficulty": "Senior Otaku",
    "category": "Bleach"
  },
  {
    "question": "Dans Fullmetal Alchemist, quel est le nom du frère d'Edward ?",
    "options": [
      "Roy Mustang",
      "Alphonse Elric",
      "Van Hohenheim",
      "Scar"
    ],
    "correct_index": 1,
    "difficulty": "Senior Otaku",
    "category": "Fullmetal Alchemist"
  },
  {
    "question": "Quel animé de studio Ghibli met en scène une fille qui travaille chez sa tante sorcière ?",
    "options": [
      "Le Voyage de Chihiro",
      "Kiki la Petite Sorcière",
      "Mon Voisin Totoro",
      "Le Château Ambulant"
    ],
    "correct_index": 1,
    "difficulty": "Senior Otaku",
    "category": "Ghibli"
  },
  {
    "question": "Dans Naruto, quel est le nom du jutsu interdit de la mort de Naruto ?",
    "options": [
      "Rasengan",
      "Chidori",
      "Flying Thunder God",
      "Shadow Clone Jutsu"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom de l'arme ultime de Luffy ?",
    "options": [
      "Gomu Gomu no: Gear 5",
      "Gomu Gomu no: Gear 4",
      "Gomu Gomu no: Gear 3",
      "Gomu Gomu no: Elephant Gun"
    ],
    "correct_index": 2,
    "category": "One Piece",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Death Note, quel est le nom du successeur de L ?",
    "options": [
      "Near et Mello",
      "Mello",
      "Near",
      "Mikami"
    ],
    "correct_index": 0,
    "category": "Death Note",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du Super Saiyan divin ?",
    "options": [
      "Super Saiyan God",
      "Super Saiyan 4",
      "Super Saiyan Blue",
      "Ultra Instinct"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Demon Slayer, quel est le nom du pilier de la flamme ?",
    "options": [
      "Rengoku Kyojuro",
      "Mitsuri Kanroji",
      "Shinobu Kocho",
      "Giyu Tomioka"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du frère de Luffy ?",
    "options": [
      "Portgas D. Ace",
      "Sabo",
      "Boa Hancock",
      "Shanks"
    ],
    "correct_index": 1,
    "category": "One Piece",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Jujutsu Kaisen, quel est le nom du roi des fléaux ?",
    "options": [
      "Ryomen Sukuna",
      "Mahito",
      "Geto",
      "Kenjaku"
    ],
    "correct_index": 0,
    "category": "Jujutsu Kaisen",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du stand de Jolyne Cujoh ?",
    "options": [
      "Stone Free",
      "Star Platinum",
      "Gold Experience",
      "Made in Heaven"
    ],
    "correct_index": 0,
    "category": "JoJo",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Hunter x Hunter, quel est le nom du président de l'association ?",
    "options": [
      "Isaac Netero",
      "Beyond Netero",
      "Pariston",
      "Cheadle"
    ],
    "correct_index": 0,
    "category": "Hunter x Hunter",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du père d'Eren Yeager ?",
    "options": [
      "Grisha Yeager",
      "Zeke Yeager",
      "Keith Shadis",
      "Dina Fritz"
    ],
    "correct_index": 0,
    "category": "Attack on Titan",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Fullmetal Alchemist, quel est le nom du grand prêtre ?",
    "options": [
      "Scar",
      "Lust",
      "Gluttony",
      "Envy"
    ],
    "correct_index": 0,
    "category": "Fullmetal Alchemist",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du démon dans Demon Slayer ?",
    "options": [
      "Muzan Kibutsuji",
      "Tanjuro",
      "Kokushibo",
      "Akaza"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Bleach, quel est le nom du capitaine de la 6e division ?",
    "options": [
      "Byakuya Kuchiki",
      "Renji Abarai",
      "Toshiro Hitsugaya",
      "Shunsui Kyoraku"
    ],
    "correct_index": 0,
    "category": "Bleach",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom de l'arme de Guerre dans Hellsing ?",
    "options": [
      "Alucard",
      "Integra",
      "Seras",
      "Walter"
    ],
    "correct_index": 0,
    "category": "Hellsing",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans One Piece, quel est le nom du père de Sanji ?",
    "options": [
      "Vinsmoke Judge",
      "Vinsmoke Ichiji",
      "Vinsmoke Niji",
      "Vinsmoke Yonji"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom de la technique de Copy Ninja Kakashi ?",
    "options": [
      "Mangekyo Sharingan",
      "Sharingan",
      "Rasengan",
      "Chidori"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Steins;Gate, quel est le nom de l'organisation rivale ?",
    "options": [
      "SERN",
      "IBM",
      "Organization of World",
      "John Titor"
    ],
    "correct_index": 0,
    "category": "Steins;Gate",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste de Shinsekai Yori ?",
    "options": [
      "Saki Watanabe",
      "Maria Akizuki",
      "Shun",
      "Satoru"
    ],
    "correct_index": 0,
    "category": "Shinsekai Yori",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Evangelion, quel est le nom du père de Shinji ?",
    "options": [
      "Gendo Ikari",
      "Kozo Fuyutsuki",
      "Ryoji Kaji",
      "Shigeru Aoba"
    ],
    "correct_index": 0,
    "category": "Evangelion",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste de Vivy ?",
    "options": [
      "Vivy",
      "Matsumoto",
      "Diva",
      "Grace"
    ],
    "correct_index": 0,
    "category": "Vivy",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans 86, quel est le nom du protagoniste ?",
    "options": [
      "Shinei Nouzen",
      "Vlad",
      "Lena",
      "Militarist"
    ],
    "correct_index": 0,
    "category": "86",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste de Vinland Saga ?",
    "options": [
      "Thorfinn",
      "Askeladd",
      "Canute",
      "Thors"
    ],
    "correct_index": 0,
    "category": "Vinland Saga",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Boku no Hero, quel est le nom du All For One ?",
    "options": [
      "All For One",
      "One For All",
      "Tomura Shigaraki",
      "All Might"
    ],
    "correct_index": 0,
    "category": "My Hero Academia",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Quel est le nom du protagoniste de Made in Abyss ?",
    "options": [
      "Riko",
      "Reg",
      "Nanachi",
      "Bondrewd"
    ],
    "correct_index": 0,
    "category": "Made in Abyss",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Dorohedoro, quel est le nom du protagoniste ?",
    "options": [
      "Caiman",
      "Nikaido",
      "En",
      "Shin"
    ],
    "correct_index": 0,
    "category": "Dorohedoro",
    "difficulty": "Master Otaku"
  },
  {
    "question": "Dans Hunter x Hunter, quel type de Nen est spécialisé dans la manipulation ?",
    "options": [
      "Emission",
      "Manipulation",
      "Matérialisation",
      "Transformation"
    ],
    "correct_index": 1,
    "difficulty": "Master Otaku",
    "category": "Hunter x Hunter"
  },
  {
    "question": "Quel est le nom du personnage principal de Cowboy Bebop ?",
    "options": [
      "Jet Black",
      "Spike Spiegel",
      "Vicious",
      "Faye Valentine"
    ],
    "correct_index": 1,
    "difficulty": "Master Otaku",
    "category": "Cowboy Bebop"
  },
  {
    "question": "Dans Evangelion, quel est le numéro de l'EVA de Shinji ?",
    "options": [
      "EVA-00",
      "EVA-01",
      "EVA-02",
      "EVA-03"
    ],
    "correct_index": 1,
    "difficulty": "Master Otaku",
    "category": "Evangelion"
  },
  {
    "question": "Quel est le véritable nom du héros dans One Punch Man ?",
    "options": [
      "Genos",
      "Saitama",
      "King",
      "Mumen Rider"
    ],
    "correct_index": 1,
    "difficulty": "Master Otaku",
    "category": "One Punch Man"
  },
  {
    "question": "Quel est le nom du vrai ennemi de Madara ?",
    "options": [
      "Kaguya Otsutsuki",
      "Hagoromo Otsutsuki",
      "Zetsu",
      "Indra Otsutsuki"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans One Piece, quel est le nom du premier royaume effacé ?",
    "options": [
      "Royaume Ancien",
      "Royaume de Lune",
      "Royaume d'Or",
      "Royaume des Cieux"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le nom du death note perdu ?",
    "options": [
      "Death Note de Rem",
      "Death Note de Ryuk",
      "Death Note de Sidoh",
      "Death Note de Gelus"
    ],
    "correct_index": 0,
    "category": "Death Note",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans Dragon Ball, quel est le nom de la transformation la plus puissante ?",
    "options": [
      "Ultra Instinct",
      "Super Saiyan 4",
      "Super Saiyan God",
      "Super Saiyan Blue"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le nom du démon le plus puissant de Demon Slayer ?",
    "options": [
      "Kokushibo",
      "Akaza",
      "Muzan Kibutsuji",
      "Doma"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans Jujutsu Kaisen, quel est le nom du mentor de Gojo ?",
    "options": [
      "Masamichi Yaga",
      "Nanami",
      "Kiyotaka Ijichi",
      "Shoko Ieiri"
    ],
    "correct_index": 0,
    "category": "Jujutsu Kaisen",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le vrai nom de Lelouch vi Britannia ?",
    "options": [
      "Lelouch vi Britannia",
      "Lelouch Lamperouge",
      "Zero",
      "Charles zi Britannia"
    ],
    "correct_index": 0,
    "category": "Code Geass",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans Attack on Titan, quel est le nom du premier mur ?",
    "options": [
      "Mur Maria",
      "Mur Rose",
      "Mur Sina",
      "Mur de Paradis"
    ],
    "correct_index": 0,
    "category": "Attack on Titan",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le nom du dieu du nouveau monde ?",
    "options": [
      "Kira (Light Yagami)",
      "L",
      "Near",
      "Mello"
    ],
    "correct_index": 0,
    "category": "Death Note",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans Bleach, quel est le nom du roi des Quincy ?",
    "options": [
      "Yhwach",
      "Jugram Haschwalth",
      "Uryu Ishida",
      "Mayuri Kurotsuchi"
    ],
    "correct_index": 0,
    "category": "Bleach",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le nom du plan de Madara ?",
    "options": [
      "Tsukuyomi Infini",
      "Plan Lune",
      "Plan Illusion",
      "Révolution des Fils"
    ],
    "correct_index": 0,
    "category": "Naruto",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans One Piece, quel est le nom du dernier outil de Kozuki ?",
    "options": [
      "Poneglyphe",
      "Ancient Weapon",
      "Pluton",
      "Poséidon"
    ],
    "correct_index": 0,
    "category": "One Piece",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le nom de la dernière forme de Frieza ?",
    "options": [
      "Golden Frieza",
      "Frieza Final Form",
      "Frieza 4th Form",
      "Frieza Perfect"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Dans Demon Slayer, quel est le nom du père de Tanjiro ?",
    "options": [
      "Tanjuro Kamado",
      "Muzan Kibutsuji",
      "Yoriichi Tsugikuni",
      "Sumiyoshi"
    ],
    "correct_index": 0,
    "category": "Demon Slayer",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quel est le nom de la dernière forme de Majin Buu ?",
    "options": [
      "Kid Buu",
      "Super Buu",
      "Fat Buu",
      "Buuhan"
    ],
    "correct_index": 0,
    "category": "Dragon Ball",
    "difficulty": "Otaku Legendaire"
  },
  {
    "question": "Quelle technique utilise le Hachimon Tonko no Jin ?",
    "options": [
      "Rasengan",
      "Chidori",
      "Sharingan",
      "Byakugan"
    ],
    "correct_index": 1,
    "difficulty": "Otaku Legendaire",
    "category": "Naruto"
  },
  {
    "question": "Dans JoJo's Bizarre Adventure, quel est le Stand de Jotaro ?",
    "options": [
      "The World",
      "Star Platinum",
      "Gold Experience",
      "Crazy Diamond"
    ],
    "correct_index": 1,
    "difficulty": "Otaku Legendaire",
    "category": "JoJo"
  },
]
DIFFICULTY_POINTS = {
    "Junior Otaku": 5,
    "Senior Otaku": 10,
    "Master Otaku": 15,
    "Otaku Legendaire": 20,
}

ADMIN_DELETE_KEY = "bnc-admin-2026"

LEVEL_THRESHOLDS = [
    (90, "SS"),
    (75, "S"),
    (55, "A"),
    (0, "B"),
]


def _get_level_index(level: str) -> int:
    try:
        return LEVEL_ORDER.index(level)
    except ValueError:
        return -1


def _is_level_unlocked(user: User, target: str) -> bool:
    target_idx = _get_level_index(target)
    if target_idx == 0:
        return True
    unlocked_idx = _get_level_index(user.highest_unlocked)
    return target_idx <= unlocked_idx


def _generate_questions_data(difficulty: str):
    pool = [q for q in _ALL_QUESTIONS if q.get("difficulty") == difficulty]
    if not pool:
        return []
    count = min(20, len(pool))
    return random.sample(pool, count)


def _score_to_grade(pct: int) -> str:
    for threshold, grade in LEVEL_THRESHOLDS:
        if pct >= threshold:
            return grade
    return "B"


@router.get("/progress", response_model=ProgressOut)
def get_progress(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProgressOut(
        highest_unlocked=user.highest_unlocked,
        completed_levels=json.loads(user.completed_levels or "[]"),
    )


@router.post("/start", response_model=StartResponse)
def start_quiz(
    difficulty: str = "Junior Otaku",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if difficulty not in LEVEL_ORDER:
            raise HTTPException(status_code=400, detail="Niveau invalide")

        if not _is_level_unlocked(user, difficulty):
            raise HTTPException(status_code=403, detail="Ce niveau n'est pas encore débloqué. Termine d'abord le niveau précédent.")

        questions_data = _generate_questions_data(difficulty)
        if not questions_data:
            raise HTTPException(status_code=500, detail=f"Aucune question disponible pour le niveau {difficulty}")

        session = ExamSession(user_id=user.id, status="in_progress", level=difficulty)
        db.add(session)
        db.flush()

        created = []
        for q in questions_data:
            qq = QuizQuestion(
                exam_session_id=session.id,
                question_text=q["question"],
                options=q["options"],
                correct_index=q["correct_index"],
                difficulty=q["difficulty"],
                category=q.get("category"),
            )
            db.add(qq)
            created.append(qq)
        db.flush()

        return StartResponse(
            session_id=session.id,
            level=difficulty,
            questions=[
                QuestionOut(
                    id=q.id,
                    question=q.question_text,
                    options=q.options,
                    difficulty=q.difficulty,
                    category=q.category,
                )
                for q in created
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur start_quiz")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/current/{session_id}", response_model=StartResponse)
def get_current_quiz(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id,
        ExamSession.user_id == user.id,
        ExamSession.status == "in_progress",
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou déjà terminée")

    questions = db.query(QuizQuestion).filter(
        QuizQuestion.exam_session_id == session_id
    ).all()

    return StartResponse(
        session_id=session.id,
        level=session.level or "",
        questions=[
            QuestionOut(
                id=q.id,
                question=q.question_text,
                options=q.options,
                difficulty=q.difficulty,
                category=q.category,
            )
            for q in questions
        ],
    )


@router.post("/submit", response_model=SubmitResponse)
def submit_quiz(
    req: SubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ExamSession).filter(
        ExamSession.id == req.session_id,
        ExamSession.user_id == user.id,
        ExamSession.status == "in_progress",
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou déjà terminée")

    questions = db.query(QuizQuestion).filter(
        QuizQuestion.exam_session_id == req.session_id
    ).all()

    if len(questions) != len(req.answers):
        raise HTTPException(status_code=400, detail="Nombre de réponses incorrect")

    total_points = 0
    earned_points = 0
    details = []

    for q, ans in zip(questions, req.answers):
        pts = DIFFICULTY_POINTS.get(q.difficulty, 10)
        total_points += pts
        is_correct = q.correct_index == ans

        ua = UserAnswer(
            user_id=user.id,
            question_id=q.id,
            selected_index=ans,
            is_correct=1 if is_correct else 0,
        )
        db.add(ua)

        if is_correct:
            earned_points += pts

        details.append({
            "question_id": q.id,
            "correct": q.correct_index,
            "selected": ans,
            "is_correct": is_correct,
            "difficulty": q.difficulty,
        })

    score_pct = round((earned_points / total_points) * 100) if total_points > 0 else 0
    grade = _score_to_grade(score_pct)
    correct_count = sum(1 for d in details if d["is_correct"])

    session.status = "completed"
    session.completed_at = None
    session.score = score_pct
    session.level = grade

    # Débloquer le niveau suivant si ≥ 55% (grade A ou mieux)
    level_name = session.level or ""
    if score_pct >= 55 and level_name:
        completed = json.loads(user.completed_levels or "[]")
        if level_name not in completed:
            completed.append(level_name)
            user.completed_levels = json.dumps(completed)

        current_idx = _get_level_index(user.highest_unlocked)
        completed_idx = _get_level_index(level_name)
        if completed_idx >= current_idx:
            next_idx = completed_idx + 1
            if next_idx < len(LEVEL_ORDER):
                user.highest_unlocked = LEVEL_ORDER[next_idx]
            else:
                user.highest_unlocked = level_name

    return SubmitResponse(
        score=score_pct,
        level=grade,
        total=len(questions),
        correct=correct_count,
        details=details,
    )


@router.delete("/admin/user/{username}")
def admin_delete_user(
    username: str,
    key: str = "",
    db: Session = Depends(get_db),
):
    if key != ADMIN_DELETE_KEY:
        raise HTTPException(status_code=403, detail="Clé admin invalide")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    return {"message": f"Utilisateur '{username}' supprimé"}


@router.post("/congratulate")
def congratulate(
    req: CongratulateRequest,
    user: User = Depends(get_current_user),
):
    try:
        from backend.services.gemini_service import gemini_quiz
        message = gemini_quiz.generate_congratulation(req.username, req.level, req.score)
    except Exception:
        message = (
            f"Félicitations {req.username} ! Tu as obtenu le niveau {req.level} avec {req.score}% !\n\n"
            f"Système d'Évaluation Autonome BNC-Otaku v2.0.\n"
            f"Protocole d'examen régi par les standards de performance établis par la Direction de Djousse Tech Evolution.\n"
            f"Ce certificat atteste de la validation des acquis conformément aux directives de qualité édictées par BeauteGar, Directeur.\n\n"
            f"Document émis par Djousse Tech Evolution — Validé par BeauteGar, Directeur."
        )

    return {"message": message}
