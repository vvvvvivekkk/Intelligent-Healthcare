"""
Local fallback AI for when OpenRouter API is unavailable.
Covers: symptoms, fitness, nutrition, wellness, lifestyle, and general health.
"""

import re

# ─── CATEGORY: SYMPTOM / MEDICAL ────────────────────────────────────

SYMPTOM_DATABASE = {
    "headache": {
        "possible_diseases": ["Tension Headache", "Migraine", "Sinusitis"],
        "confidence_level": "medium",
        "recommended_specialization": "Neurology",
        "basic_advice": "Rest in a quiet, dark room. Stay hydrated. Take over-the-counter pain relief like acetaminophen or ibuprofen. If headaches persist or worsen, consult a neurologist.",
        "follow_up_questions": ["How long have you had this headache?", "Is the pain on one side or both sides?", "Do you experience nausea or sensitivity to light?"],
    },
    "fever": {
        "possible_diseases": ["Viral Infection", "Common Flu", "COVID-19"],
        "confidence_level": "medium",
        "recommended_specialization": "General Medicine",
        "basic_advice": "Rest, stay hydrated, and monitor your temperature. Take acetaminophen to reduce fever. If fever exceeds 103°F (39.4°C) or lasts more than 3 days, seek medical attention.",
        "follow_up_questions": ["What is your current temperature?", "How long have you had the fever?", "Do you have any other symptoms like cough or body aches?"],
    },
    "cough": {
        "possible_diseases": ["Common Cold", "Bronchitis", "Allergic Rhinitis"],
        "confidence_level": "medium",
        "recommended_specialization": "Pulmonology",
        "basic_advice": "Stay hydrated with warm fluids. Use honey and lemon in warm water. Avoid irritants like smoke. If cough persists beyond 2 weeks or produces blood, see a doctor.",
        "follow_up_questions": ["Is your cough dry or productive (with mucus)?", "How long have you been coughing?", "Do you have difficulty breathing?"],
    },
    "stomach pain": {
        "possible_diseases": ["Gastritis", "Acid Reflux (GERD)", "Irritable Bowel Syndrome"],
        "confidence_level": "medium",
        "recommended_specialization": "Gastroenterology",
        "basic_advice": "Avoid spicy, fatty, and acidic foods. Eat smaller meals. Stay upright after eating. Over-the-counter antacids may help. See a gastroenterologist if pain is severe or persistent.",
        "follow_up_questions": ["Where exactly is the pain located?", "Is the pain related to eating?", "Do you experience nausea, vomiting, or bloating?"],
    },
    "chest pain": {
        "possible_diseases": ["Angina", "Costochondritis", "Acid Reflux"],
        "confidence_level": "low",
        "recommended_specialization": "Cardiology",
        "basic_advice": "⚠️ IMPORTANT: If you experience sudden, severe chest pain, especially with shortness of breath, pain radiating to arm/jaw, or sweating, CALL EMERGENCY SERVICES IMMEDIATELY.",
        "follow_up_questions": ["Is the pain sharp or dull?", "Does it worsen with breathing or movement?", "Do you have shortness of breath?"],
    },
    "back pain": {
        "possible_diseases": ["Muscle Strain", "Herniated Disc", "Poor Posture"],
        "confidence_level": "medium",
        "recommended_specialization": "Orthopedics",
        "basic_advice": "Apply ice for the first 48 hours, then switch to heat. Gentle stretching may help. Maintain good posture. Over-the-counter pain relievers can provide relief.",
        "follow_up_questions": ["Where is the pain located?", "Did it start after an injury?", "Does the pain radiate to your legs?"],
    },
    "sore throat": {
        "possible_diseases": ["Pharyngitis", "Tonsillitis", "Common Cold"],
        "confidence_level": "medium",
        "recommended_specialization": "ENT (Otolaryngology)",
        "basic_advice": "Gargle with warm salt water. Stay hydrated with warm fluids. Use throat lozenges. If it lasts more than a week or is accompanied by high fever, see a doctor.",
        "follow_up_questions": ["How long have you had the sore throat?", "Do you have difficulty swallowing?", "Do you have fever or swollen glands?"],
    },
    "skin rash": {
        "possible_diseases": ["Contact Dermatitis", "Eczema", "Allergic Reaction"],
        "confidence_level": "medium",
        "recommended_specialization": "Dermatology",
        "basic_advice": "Avoid scratching. Apply calamine lotion or hydrocortisone cream. Take antihistamines for itching. If it spreads rapidly or shows signs of infection, seek medical attention.",
        "follow_up_questions": ["When did the rash first appear?", "Is it itchy or painful?", "Have you been exposed to any new products?"],
    },
    "joint pain": {
        "possible_diseases": ["Osteoarthritis", "Rheumatoid Arthritis", "Gout"],
        "confidence_level": "medium",
        "recommended_specialization": "Rheumatology",
        "basic_advice": "Rest the affected joint. Apply ice to reduce swelling. Over-the-counter anti-inflammatory medications may help. See a rheumatologist for persistent pain.",
        "follow_up_questions": ["Which joints are affected?", "Is there swelling?", "Is the pain worse in the morning?"],
    },
    "breathing difficulty": {
        "possible_diseases": ["Asthma", "Bronchitis", "Anxiety"],
        "confidence_level": "low",
        "recommended_specialization": "Pulmonology",
        "basic_advice": "⚠️ If severe, CALL EMERGENCY SERVICES. For mild symptoms, stay calm, sit upright, take slow breaths. Use prescribed inhalers if available.",
        "follow_up_questions": ["Is the difficulty sudden or gradual?", "Do you have a history of asthma?", "Is it accompanied by wheezing?"],
    },
    "dizziness": {
        "possible_diseases": ["Vertigo (BPPV)", "Low Blood Pressure", "Anemia"],
        "confidence_level": "medium",
        "recommended_specialization": "Neurology",
        "basic_advice": "Sit or lie down if feeling dizzy. Stay hydrated and avoid sudden position changes. If dizziness is severe or frequent, seek medical evaluation.",
        "follow_up_questions": ["Does the room seem to spin?", "Do you feel lightheaded?", "When does it occur?"],
    },
    "fatigue": {
        "possible_diseases": ["Iron Deficiency Anemia", "Thyroid Disorder", "Sleep Disorder"],
        "confidence_level": "low",
        "recommended_specialization": "General Medicine",
        "basic_advice": "Ensure 7-9 hours of quality sleep. Maintain a balanced diet rich in iron and vitamins. Exercise regularly. If fatigue persists, blood tests can identify causes.",
        "follow_up_questions": ["How long have you been feeling fatigued?", "Are you sleeping well?", "Any other symptoms like weight changes?"],
    },
    "nausea": {
        "possible_diseases": ["Gastroenteritis", "Food Poisoning", "Motion Sickness"],
        "confidence_level": "medium",
        "recommended_specialization": "Gastroenterology",
        "basic_advice": "Sip clear fluids slowly. Avoid solid foods until nausea subsides. Ginger tea or peppermint may help. If vomiting persists beyond 24 hours, seek medical attention.",
        "follow_up_questions": ["Are you also vomiting?", "Did you eat anything unusual?", "Is the nausea constant?"],
    },
    "insomnia": {
        "possible_diseases": ["Primary Insomnia", "Sleep Apnea", "Restless Leg Syndrome"],
        "confidence_level": "medium",
        "recommended_specialization": "Neurology",
        "basic_advice": "Maintain a consistent sleep schedule. Avoid screens 1 hour before bed. Keep your bedroom cool, dark, and quiet. Limit caffeine after noon.",
        "follow_up_questions": ["Trouble falling or staying asleep?", "How long has this been happening?", "Do you snore?"],
    },
    "anxiety": {
        "possible_diseases": ["Generalized Anxiety Disorder", "Panic Disorder", "Stress-related Anxiety"],
        "confidence_level": "low",
        "recommended_specialization": "Psychiatry",
        "basic_advice": "Practice deep breathing (4-7-8 technique). Regular exercise, adequate sleep, and limiting caffeine help. Consider speaking with a mental health professional.",
        "follow_up_questions": ["How long have you been anxious?", "Do you have panic attacks?", "Is it affecting daily activities?"],
    },
    "toothache": {
        "possible_diseases": ["Dental Cavity", "Tooth Abscess", "Gum Disease"],
        "confidence_level": "medium",
        "recommended_specialization": "Dentistry",
        "basic_advice": "Rinse with warm salt water. Apply a cold compress. OTC pain relievers can help temporarily. See a dentist as soon as possible.",
        "follow_up_questions": ["Is the pain constant?", "Any swelling?", "Sensitive to hot or cold?"],
    },
    "eye pain": {
        "possible_diseases": ["Eye Strain", "Conjunctivitis", "Dry Eye Syndrome"],
        "confidence_level": "medium",
        "recommended_specialization": "Ophthalmology",
        "basic_advice": "Rest your eyes (20-20-20 rule). Use artificial tears for dryness. Avoid rubbing. See an ophthalmologist if pain persists.",
        "follow_up_questions": ["One or both eyes?", "Redness or discharge?", "Long screen hours?"],
    },
    "ear pain": {
        "possible_diseases": ["Otitis Media (Middle Ear Infection)", "Otitis Externa (Swimmer's Ear)", "Eustachian Tube Dysfunction"],
        "confidence_level": "medium",
        "recommended_specialization": "ENT (Otolaryngology)",
        "basic_advice": "Apply a warm compress to the affected ear. Over-the-counter pain relievers like ibuprofen or acetaminophen can help. Avoid inserting objects into the ear. If pain persists beyond 2-3 days, is severe, or is accompanied by fever or discharge, see an ENT specialist.",
        "follow_up_questions": ["Is the pain in one or both ears?", "Do you have any discharge or fluid from the ear?", "Do you have fever, hearing loss, or a feeling of fullness in the ear?"],
    },
}

# Keyword aliases for symptom matching
SYMPTOM_ALIASES = {
    "head pain": "headache", "head ache": "headache", "headace": "headache",
    "migraine": "headache", "temperature": "fever", "feverish": "fever",
    "flu": "fever", "tummy ache": "stomach pain", "stomach ache": "stomach pain",
    "belly pain": "stomach pain", "abdominal pain": "stomach pain",
    "heart pain": "chest pain", "chest tightness": "chest pain",
    "lower back pain": "back pain", "upper back pain": "back pain",
    "spine pain": "back pain", "throat pain": "sore throat",
    "itchy skin": "skin rash", "rash": "skin rash", "hives": "skin rash",
    "knee pain": "joint pain", "shoulder pain": "joint pain",
    "hip pain": "joint pain", "elbow pain": "joint pain",
    "shortness of breath": "breathing difficulty", "cant breathe": "breathing difficulty",
    "breathless": "breathing difficulty", "wheezing": "breathing difficulty",
    "lightheaded": "dizziness", "vertigo": "dizziness", "faint": "dizziness",
    "tired": "fatigue", "exhausted": "fatigue", "no energy": "fatigue",
    "weak": "fatigue", "eye strain": "eye pain", "blurry vision": "eye pain",
    "stressed": "anxiety", "panic": "anxiety", "nervous": "anxiety",
    "depressed": "anxiety", "vomiting": "nausea", "throwing up": "nausea",
    "cant sleep": "insomnia", "sleep problems": "insomnia",
    "not sleeping": "insomnia", "tooth pain": "toothache",
    "difficulty breathing": "breathing difficulty",
    "trouble breathing": "breathing difficulty",
    "body aches": "joint pain", "body pain": "joint pain",
    "runny nose": "cough", "sneezing": "cough", "congestion": "cough",
    "earache": "ear pain", "ear ache": "ear pain", "ear infection": "ear pain",
    "ear ringing": "ear pain", "tinnitus": "ear pain", "ear blocked": "ear pain",
    "ear hurts": "ear pain", "ear discharge": "ear pain",
    "suffering from": "",
}


# ─── CATEGORY: FITNESS & EXERCISE ───────────────────────────────────

FITNESS_TOPICS = {
    "weight loss": {
        "title": "🏋️ Weight Loss Guide",
        "response": (
            "Here's a practical approach to healthy weight loss:\n\n"
            "**Nutrition (most important — 80% of results):**\n"
            "• Create a calorie deficit of 300-500 calories/day (gradual and sustainable)\n"
            "• Focus on high-protein foods (eggs, chicken, lentils, paneer, fish)\n"
            "• Eat plenty of vegetables and whole grains\n"
            "• Reduce sugar, fried foods, and processed snacks\n"
            "• Drink 3-4 liters of water daily\n\n"
            "**Exercise (20% of results but crucial for health):**\n"
            "• Start with 30 min brisk walking daily\n"
            "• Add 3-4 strength training sessions/week (bodyweight exercises work great)\n"
            "• Try HIIT 2x/week for efficient fat burning\n"
            "• Stay consistent — aim for 150 min of moderate activity per week\n\n"
            "**Lifestyle:**\n"
            "• Sleep 7-8 hours — poor sleep increases hunger hormones\n"
            "• Track your food for awareness (apps like MyFitnessPal)\n"
            "• Be patient — aim for 0.5-1 kg loss per week\n\n"
            "Would you like a specific workout plan or meal plan?"
        ),
    },
    "weight gain": {
        "title": "💪 Healthy Weight Gain Guide",
        "response": (
            "Here's how to gain weight healthily:\n\n"
            "**Nutrition:**\n"
            "• Eat in a calorie surplus of 300-500 calories/day\n"
            "• Increase protein intake to 1.6-2.2g per kg of body weight\n"
            "• Eat calorie-dense foods: nuts, peanut butter, bananas, oats, whole milk, cheese\n"
            "• Have 5-6 smaller meals instead of 3 large ones\n"
            "• Post-workout shake: banana + oats + milk + peanut butter\n\n"
            "**Exercise:**\n"
            "• Focus on compound exercises: squats, deadlifts, bench press, pull-ups\n"
            "• Train 4-5 days/week with progressive overload\n"
            "• Keep cardio minimal (2x/week, 15-20 min)\n"
            "• Rest 48 hours between muscle groups\n\n"
            "**Lifestyle:**\n"
            "• Sleep 7-9 hours for optimal muscle recovery\n"
            "• Stay hydrated\n"
            "• Be consistent — muscle gain takes 3-6 months of effort\n\n"
            "Want a specific workout split or meal plan?"
        ),
    },
    "muscle gain": {
        "title": "💪 Muscle Building Guide",
        "response": (
            "Here's a science-backed approach to building muscle:\n\n"
            "**Training (Progressive Overload is Key):**\n"
            "• Train each muscle group 2x/week\n"
            "• Focus on compound lifts: squat, bench, deadlift, overhead press, rows\n"
            "• 3-4 sets of 8-12 reps per exercise\n"
            "• Increase weight or reps each week\n"
            "• Rest 60-90 seconds between sets\n\n"
            "**Nutrition:**\n"
            "• Protein: 1.6-2.2g per kg bodyweight daily\n"
            "• Best sources: chicken, eggs, fish, lentils, paneer, whey protein\n"
            "• Eat in a slight calorie surplus (+300 cal)\n"
            "• Carbs around workouts for energy\n\n"
            "**Recovery:**\n"
            "• Sleep 7-9 hours — muscle grows during sleep\n"
            "• Rest day between intense sessions\n"
            "• Stay hydrated (3-4L water daily)\n\n"
            "**Sample Split:**\n"
            "• Day 1: Chest + Triceps\n"
            "• Day 2: Back + Biceps\n"
            "• Day 3: Rest\n"
            "• Day 4: Legs + Shoulders\n"
            "• Day 5: Full Body\n"
            "• Day 6-7: Rest/Light cardio\n\n"
            "Would you like more detail on any specific exercise or body part?"
        ),
    },
    "workout": {
        "title": "🏃 Workout Recommendations",
        "response": (
            "Here are workout options based on your goals:\n\n"
            "**For Beginners (No Equipment Needed):**\n"
            "• 20 Push-ups (or knee push-ups)\n"
            "• 30 Squats\n"
            "• 30-sec Plank\n"
            "• 20 Lunges (each leg)\n"
            "• 15 Burpees\n"
            "• 1-min Jumping Jacks\n"
            "• Do 3 rounds with 1-min rest between rounds\n\n"
            "**For Intermediates:**\n"
            "• Monday: Upper body (push-ups, dips, shoulder press)\n"
            "• Tuesday: Lower body (squats, lunges, calf raises)\n"
            "• Wednesday: Cardio (running, cycling, jump rope)\n"
            "• Thursday: Core (planks, crunches, leg raises)\n"
            "• Friday: Full body circuit\n"
            "• Weekend: Active recovery (walking, yoga)\n\n"
            "**Quick Tips:**\n"
            "• Always warm up for 5-10 minutes\n"
            "• Start slow and build up gradually\n"
            "• Consistency beats intensity\n"
            "• 30-45 minutes is plenty\n\n"
            "Want a plan tailored to your specific goal (fat loss, strength, endurance)?"
        ),
    },
    "yoga": {
        "title": "🧘 Yoga & Flexibility Guide",
        "response": (
            "Yoga is excellent for both physical and mental health!\n\n"
            "**Beginner Routine (20 min daily):**\n"
            "1. **Mountain Pose (Tadasana)** — 1 min (posture awareness)\n"
            "2. **Cat-Cow Stretch** — 10 reps (spine mobility)\n"
            "3. **Downward Dog** — 30 sec (full body stretch)\n"
            "4. **Warrior I & II** — 30 sec each side (leg strength)\n"
            "5. **Tree Pose** — 30 sec each side (balance)\n"
            "6. **Cobra Pose** — 30 sec (back flexibility)\n"
            "7. **Child's Pose** — 1 min (relaxation)\n"
            "8. **Shavasana** — 3 min (deep rest)\n\n"
            "**Benefits:**\n"
            "• Reduces stress and anxiety\n"
            "• Improves flexibility and posture\n"
            "• Strengthens core and balance\n"
            "• Better sleep quality\n"
            "• Helps with back pain\n\n"
            "**Tips:**\n"
            "• Practice on an empty stomach (morning is best)\n"
            "• Use a yoga mat for comfort\n"
            "• Focus on breathing — inhale through nose, exhale through mouth\n"
            "• Don't force stretches; progress gradually\n\n"
            "Would you like a specific yoga routine for stress, back pain, or flexibility?"
        ),
    },
    "running": {
        "title": "🏃 Running Guide",
        "response": (
            "Running is one of the best cardiovascular exercises!\n\n"
            "**Beginner Plan (Couch to 5K concept):**\n"
            "• Week 1-2: Walk 5 min, jog 1 min, repeat 5x\n"
            "• Week 3-4: Walk 3 min, jog 3 min, repeat 4x\n"
            "• Week 5-6: Walk 2 min, jog 5 min, repeat 3x\n"
            "• Week 7-8: Continuous jog for 20-30 minutes\n\n"
            "**Tips for Runners:**\n"
            "• Invest in good running shoes\n"
            "• Warm up with 5 min brisk walk\n"
            "• Focus on breathing — inhale nose, exhale mouth\n"
            "• Land on midfoot, not heel\n"
            "• Don't increase distance more than 10% per week\n"
            "• Hydrate before and after\n"
            "• Cool down with stretching\n\n"
            "**Benefits:**\n"
            "• Burns 400-600 calories per hour\n"
            "• Improves cardiovascular health\n"
            "• Boosts mood (runner's high!)\n"
            "• Strengthens bones and muscles\n\n"
            "Would you like a specific training plan for a distance goal?"
        ),
    },
    "stretching": {
        "title": "🤸 Stretching & Flexibility",
        "response": (
            "Regular stretching improves mobility and prevents injuries!\n\n"
            "**Daily Stretching Routine (10 min):**\n"
            "1. Neck rolls — 30 sec each direction\n"
            "2. Shoulder rolls — 30 sec\n"
            "3. Arm cross stretch — 20 sec each arm\n"
            "4. Standing quad stretch — 20 sec each leg\n"
            "5. Hamstring stretch (toe touch) — 30 sec\n"
            "6. Hip flexor stretch — 20 sec each side\n"
            "7. Cat-Cow back stretch — 10 reps\n"
            "8. Butterfly stretch — 30 sec\n"
            "9. Seated spinal twist — 20 sec each side\n"
            "10. Child's pose — 1 min\n\n"
            "**Tips:**\n"
            "• Stretch after warming up (never stretch cold muscles)\n"
            "• Hold each stretch for 15-30 seconds\n"
            "• Breathe deeply — don't hold your breath\n"
            "• Never bounce in a stretch\n"
            "• Stretch daily or at least after every workout\n\n"
            "Want me to suggest stretches for a specific body part?"
        ),
    },
}


# ─── CATEGORY: NUTRITION & DIET ─────────────────────────────────────

NUTRITION_TOPICS = {
    "diet plan": {
        "title": "🥗 Balanced Diet Plan",
        "response": (
            "Here's a balanced daily meal plan:\n\n"
            "**Morning (7-8 AM):**\n"
            "• Option A: Oatmeal with banana, nuts, and honey\n"
            "• Option B: 2 eggs + whole wheat toast + fruit\n"
            "• Option C: Greek yogurt with granola and berries\n\n"
            "**Mid-Morning Snack (10-11 AM):**\n"
            "• A handful of almonds or walnuts\n"
            "• An apple or banana\n\n"
            "**Lunch (1-2 PM):**\n"
            "• Brown rice / roti + dal / chicken + salad + veggies\n"
            "• Include a variety of colorful vegetables\n\n"
            "**Evening Snack (4-5 PM):**\n"
            "• Green tea + a fruit or light sandwich\n"
            "• Sprouts salad or hummus with veggies\n\n"
            "**Dinner (7-8 PM):**\n"
            "• Light meal: soup + salad + grilled protein\n"
            "• Or: roti + sabzi + curd\n"
            "• Avoid heavy carbs at night\n\n"
            "**Key Principles:**\n"
            "• Eat every 3-4 hours to maintain metabolism\n"
            "• Drink 3-4 liters of water daily\n"
            "• Limit sugar, processed foods, and fried items\n"
            "• Include protein in every meal\n\n"
            "Would you like a plan customized for a specific goal (weight loss, gain, or maintenance)?"
        ),
    },
    "protein": {
        "title": "🥩 Protein Guide",
        "response": (
            "Protein is essential for muscle repair, immunity, and overall health.\n\n"
            "**How Much Protein Do You Need?**\n"
            "• Sedentary adults: 0.8g per kg body weight\n"
            "• Active / gym-goers: 1.2-1.6g per kg\n"
            "• Muscle building: 1.6-2.2g per kg\n"
            "• Example: 70 kg person building muscle → 112-154g protein/day\n\n"
            "**Best Protein Sources:**\n"
            "• 🥚 Eggs — 6g per egg (cheapest quality protein)\n"
            "• 🍗 Chicken breast — 31g per 100g\n"
            "• 🐟 Fish — 20-25g per 100g\n"
            "• 🥛 Greek yogurt — 10g per 100g\n"
            "• 🫘 Lentils (dal) — 9g per 100g cooked\n"
            "• 🧀 Paneer — 18g per 100g\n"
            "• 🥜 Peanuts — 26g per 100g\n"
            "• 🌱 Chickpeas — 19g per 100g\n"
            "• Whey protein shake — 24-30g per scoop\n\n"
            "**Tips:**\n"
            "• Spread protein across 4-5 meals\n"
            "• Have protein within 30 min after workout\n"
            "• Combine plant proteins for complete amino acids\n\n"
            "Any specific questions about protein or supplements?"
        ),
    },
    "hydration": {
        "title": "💧 Hydration Guide",
        "response": (
            "Staying hydrated is crucial for every body function!\n\n"
            "**How Much Water?**\n"
            "• General: 2.5-3.5 liters/day (8-12 glasses)\n"
            "• Active / exercising: 3.5-5 liters/day\n"
            "• Hot climate: add 1-2 extra glasses\n\n"
            "**Signs of Dehydration:**\n"
            "• Dark yellow urine\n"
            "• Dry mouth and lips\n"
            "• Fatigue and headaches\n"
            "• Dizziness\n"
            "• Poor concentration\n\n"
            "**Hydration Tips:**\n"
            "• Start your day with 2 glasses of water\n"
            "• Carry a water bottle everywhere\n"
            "• Eat water-rich foods (cucumber, watermelon, oranges)\n"
            "• Set hourly reminders if you forget\n"
            "• Drink before, during, and after exercise\n"
            "• Herbal teas and coconut water count too\n"
            "• Reduce caffeine and alcohol — they dehydrate you\n\n"
            "Your urine should be light yellow — that's the easiest hydration check!"
        ),
    },
    "vitamins": {
        "title": "💊 Vitamins & Minerals Guide",
        "response": (
            "Here are the key vitamins and minerals your body needs:\n\n"
            "**Essential Vitamins:**\n"
            "• **Vitamin D** — Sunlight (15-20 min morning sun), fish, fortified milk. Crucial for bones and immunity.\n"
            "• **Vitamin C** — Citrus fruits, bell peppers, guava. Boosts immunity and skin health.\n"
            "• **Vitamin B12** — Eggs, dairy, meat. Essential for energy and nerve function.\n"
            "• **Vitamin A** — Carrots, sweet potatoes, spinach. Good for eyes and skin.\n"
            "• **Vitamin E** — Nuts, seeds, oils. Antioxidant protection.\n\n"
            "**Key Minerals:**\n"
            "• **Iron** — Spinach, lentils, red meat. Prevents anemia.\n"
            "• **Calcium** — Milk, yogurt, cheese, leafy greens. Strong bones.\n"
            "• **Zinc** — Nuts, seeds, chickpeas. Immunity and healing.\n"
            "• **Magnesium** — Bananas, dark chocolate, almonds. Muscle and nerve function.\n\n"
            "**Tips:**\n"
            "• Get nutrients from whole foods first, supplements second\n"
            "• Get blood work done yearly to check for deficiencies\n"
            "• Vitamin D and B12 are commonly deficient — consider supplementing\n\n"
            "Would you like advice on supplements for a specific concern?"
        ),
    },
    "healthy eating": {
        "title": "🍎 Healthy Eating Fundamentals",
        "response": (
            "Here are the core principles of healthy eating:\n\n"
            "**The Plate Rule:**\n"
            "• 50% vegetables and fruits\n"
            "• 25% lean protein (chicken, fish, lentils, tofu)\n"
            "• 25% complex carbs (brown rice, whole wheat, oats)\n"
            "• Add healthy fats (olive oil, nuts, avocado)\n\n"
            "**Foods to Include Daily:**\n"
            "✅ Leafy greens, seasonal vegetables\n"
            "✅ Fresh fruits (2-3 servings)\n"
            "✅ Whole grains\n"
            "✅ Lean protein\n"
            "✅ Nuts and seeds\n"
            "✅ Yogurt/curd\n\n"
            "**Foods to Limit:**\n"
            "❌ Sugar and sugary drinks\n"
            "❌ Deep-fried foods\n"
            "❌ Processed/packaged snacks\n"
            "❌ White bread, maida products\n"
            "❌ Excessive salt\n\n"
            "**Healthy Habits:**\n"
            "• Eat slowly and mindfully\n"
            "• Don't skip breakfast\n"
            "• Cook at home more often\n"
            "• Read nutrition labels\n"
            "• Stop eating when 80% full\n\n"
            "Need a specific meal plan?"
        ),
    },
}

# ─── CATEGORY: LIFESTYLE & WELLNESS ─────────────────────────────────

WELLNESS_TOPICS = {
    "sleep": {
        "title": "😴 Better Sleep Guide",
        "response": (
            "Quality sleep is the foundation of good health!\n\n"
            "**How Much Sleep Do You Need?**\n"
            "• Adults: 7-9 hours per night\n"
            "• Teens: 8-10 hours\n"
            "• Quality matters as much as quantity\n\n"
            "**Sleep Hygiene Tips:**\n"
            "1. **Fixed schedule** — Sleep and wake at the same time daily, even weekends\n"
            "2. **Dark room** — Use blackout curtains or an eye mask\n"
            "3. **Cool temperature** — Keep bedroom at 18-22°C\n"
            "4. **No screens** — Stop phone/laptop 1 hour before bed\n"
            "5. **No caffeine** after 2 PM\n"
            "6. **Wind-down routine** — Read, stretch, or meditate before bed\n"
            "7. **Avoid heavy meals** close to bedtime\n"
            "8. **Limit naps** to 20 min before 3 PM\n\n"
            "**Natural Sleep Aids:**\n"
            "• Chamomile tea before bed\n"
            "• Warm milk with turmeric\n"
            "• Lavender essential oil\n"
            "• Magnesium-rich foods (bananas, almonds)\n"
            "• 4-7-8 breathing technique\n\n"
            "Consistent sleep transforms your energy, mood, and health!"
        ),
    },
    "stress": {
        "title": "🧠 Stress Management",
        "response": (
            "Here are proven strategies to manage stress:\n\n"
            "**Immediate Relief (do right now):**\n"
            "• **Box breathing** — Inhale 4s → hold 4s → exhale 4s → hold 4s. Repeat 5x\n"
            "• **5-4-3-2-1 grounding** — Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste\n"
            "• **Progressive muscle relaxation** — Tense and release each muscle group\n\n"
            "**Daily Habits for Stress Reduction:**\n"
            "• Exercise 30 min daily (walking counts!)\n"
            "• Practice 10 min meditation or deep breathing\n"
            "• Spend time in nature\n"
            "• Limit social media to 30 min/day\n"
            "• Journal your thoughts for 5 min before bed\n"
            "• Talk to friends or family regularly\n"
            "• Listen to calming music\n\n"
            "**Lifestyle Changes:**\n"
            "• Identify and manage your stress triggers\n"
            "• Learn to say 'no' and set boundaries\n"
            "• Break large tasks into small steps\n"
            "• Get adequate sleep (7-8 hours)\n"
            "• Reduce caffeine and alcohol\n\n"
            "If stress is overwhelming or persistent, consider speaking with a counselor or therapist. There's no shame in asking for help! 💛"
        ),
    },
    "energy": {
        "title": "⚡ Boost Your Energy",
        "response": (
            "Feeling low on energy? Here's how to fix it naturally:\n\n"
            "**Morning Energy Boost:**\n"
            "• Wake up at a consistent time\n"
            "• Get 10 min of sunlight within 30 min of waking\n"
            "• Hydrate first — 2 glasses of water before coffee\n"
            "• Eat a protein-rich breakfast\n"
            "• Do 5-10 min light exercise or stretching\n\n"
            "**Throughout the Day:**\n"
            "• Take short walks every 60-90 minutes\n"
            "• Snack on nuts, fruits, or dark chocolate\n"
            "• Stay hydrated (dehydration = fatigue)\n"
            "• Power nap 15-20 min after lunch if needed\n"
            "• Use cold water on face/wrists for alertness\n\n"
            "**Avoid Energy Killers:**\n"
            "❌ Sugar crashes (candy, soda, white bread)\n"
            "❌ Excessive caffeine (more than 3 cups)\n"
            "❌ Heavy carb-only meals\n"
            "❌ Sitting for hours without moving\n"
            "❌ Dehydration\n\n"
            "**Energy-Boosting Foods:**\n"
            "• Bananas, oats, almonds, eggs, green tea\n"
            "• Iron-rich foods (spinach, lentils)\n"
            "• Complex carbs + protein combos\n\n"
            "If low energy persists despite good habits, consider getting blood work (check iron, B12, thyroid, vitamin D)."
        ),
    },
    "productivity": {
        "title": "🎯 Productivity & Focus",
        "response": (
            "Here's how to maximize your productivity:\n\n"
            "**Time Management Techniques:**\n"
            "• **Pomodoro** — Work 25 min, break 5 min. After 4 rounds, take 15-30 min break\n"
            "• **Time blocking** — Assign specific tasks to specific hours\n"
            "• **2-minute rule** — If a task takes < 2 min, do it immediately\n"
            "• **Eat the frog** — Do the hardest task first thing in the morning\n\n"
            "**Focus Hacks:**\n"
            "• Put phone in another room while working\n"
            "• Use website blockers during focus time\n"
            "• Work in 90-minute deep work sessions\n"
            "• Listen to lo-fi or binaural beats\n"
            "• Keep a to-do list (max 3 priorities per day)\n\n"
            "**Physical Support for Productivity:**\n"
            "• Sleep 7-8 hours (non-negotiable)\n"
            "• Exercise in the morning for mental clarity\n"
            "• Stay hydrated and eat brain-healthy foods\n"
            "• Take regular breaks to avoid burnout\n"
            "• Get sunlight exposure during the day\n\n"
            "**Evening Wind-Down:**\n"
            "• Plan tomorrow's priorities before bed\n"
            "• Review what you accomplished today\n"
            "• Digital detox 1 hour before sleep\n\n"
            "What specific area do you want to improve — studying, work, or daily routine?"
        ),
    },
    "mental health": {
        "title": "💛 Mental Health & Wellbeing",
        "response": (
            "Taking care of your mental health is just as important as physical health.\n\n"
            "**Daily Mental Health Practices:**\n"
            "• Start the day with gratitude — list 3 things you're grateful for\n"
            "• Meditate for 5-10 minutes (try apps like Headspace or Calm)\n"
            "• Get at least 30 min of physical activity\n"
            "• Spend time outdoors and in nature\n"
            "• Connect with someone you care about\n"
            "• Limit news and social media consumption\n"
            "• Journal your thoughts and feelings\n\n"
            "**When to Seek Professional Help:**\n"
            "• Persistent sadness lasting more than 2 weeks\n"
            "• Loss of interest in activities you used to enjoy\n"
            "• Difficulty sleeping or sleeping too much\n"
            "• Feeling hopeless or worthless\n"
            "• Difficulty concentrating or making decisions\n"
            "• Thoughts of self-harm\n\n"
            "**Remember:**\n"
            "• It's okay to not be okay\n"
            "• Asking for help is a sign of strength\n"
            "• Mental health is a spectrum — everyone has ups and downs\n"
            "• Professional support (therapy) works and is worth trying\n\n"
            "If you're in crisis, please reach out to a mental health helpline: **Vandrevala Foundation: 1860-2662-345** (India) or your local crisis line. 💛"
        ),
    },
    "morning routine": {
        "title": "🌅 Optimal Morning Routine",
        "response": (
            "A great morning sets the tone for the whole day!\n\n"
            "**Suggested Morning Routine (Adaptable):**\n\n"
            "⏰ **Wake up** — Same time daily, avoid snoozing\n\n"
            "💧 **Hydrate** (0-5 min) — Drink 2 glasses of water\n\n"
            "🧘 **Move** (5-15 min) — Stretching, yoga, or a short walk\n\n"
            "🧠 **Mindfulness** (15-20 min) — Meditate, journal, or practice gratitude\n\n"
            "🚿 **Freshen up** (20-30 min) — Cold shower for alertness (optional!)\n\n"
            "🍳 **Breakfast** (30-45 min) — Protein-rich, balanced meal\n\n"
            "📋 **Plan** (45-50 min) — Review your top 3 priorities for the day\n\n"
            "**Key Principles:**\n"
            "• No phone for the first 30 minutes\n"
            "• Get sunlight within 30 min of waking\n"
            "• Do something for your body and mind before work\n"
            "• Keep it consistent — routine beats motivation\n\n"
            "Start with just 2-3 of these habits and build up gradually. What matters is consistency, not perfection!"
        ),
    },
    "staying active": {
        "title": "🏃 Staying Active Throughout the Day",
        "response": (
            "You don't need a gym to stay active! Here are practical tips:\n\n"
            "**At College / Office:**\n"
            "• Take the stairs instead of elevator\n"
            "• Walk during phone calls\n"
            "• Stand up and stretch every 30-45 minutes\n"
            "• Walk to a colleague's desk instead of messaging\n"
            "• Use a standing desk if available\n"
            "• Do desk exercises (shoulder rolls, leg raises, calf raises)\n\n"
            "**Between Classes / Work:**\n"
            "• Walk briskly between buildings\n"
            "• Do 10 squats during breaks\n"
            "• Stretch your neck and shoulders\n"
            "• Use a study break for a 10-min walk outside\n\n"
            "**Daily Movement Goals:**\n"
            "• Aim for 8,000-10,000 steps daily\n"
            "• 30 min of intentional movement (walk, cycle, sports)\n"
            "• Reduce sitting time — move every 45 min\n\n"
            "**Fun Activities:**\n"
            "• Join a sports club or group fitness class\n"
            "• Cycle to college/work\n"
            "• Play a sport with friends on weekends\n"
            "• Dance — it's great cardio!\n"
            "• Take up swimming, martial arts, or hiking\n\n"
            "The best exercise is the one you enjoy and can do consistently!"
        ),
    },
    "skin care": {
        "title": "✨ Skincare Basics",
        "response": (
            "A simple, consistent skincare routine works best:\n\n"
            "**Basic Daily Routine:**\n"
            "1. **Cleanser** — Wash face morning and night with a gentle cleanser\n"
            "2. **Moisturizer** — Apply even if you have oily skin\n"
            "3. **Sunscreen** — SPF 30+ every morning (most important step!)\n\n"
            "**For Acne-Prone Skin:**\n"
            "• Use a salicylic acid or niacinamide cleanser\n"
            "• Don't touch or pick at pimples\n"
            "• Change pillowcase weekly\n"
            "• Reduce dairy and sugary foods\n\n"
            "**For Healthy Glowing Skin:**\n"
            "• Drink plenty of water (3+ liters/day)\n"
            "• Eat fruits and vegetables rich in Vitamin C and E\n"
            "• Sleep 7-8 hours\n"
            "• Exercise regularly (improves circulation)\n"
            "• Manage stress\n\n"
            "**Tips:**\n"
            "• Less is more — don't overload with products\n"
            "• Patch-test new products\n"
            "• Be patient — skincare takes 4-6 weeks to show results\n"
            "• See a dermatologist for persistent skin issues\n\n"
            "Would you like specific product or routine recommendations?"
        ),
    },
    "hair care": {
        "title": "💇 Hair Care Tips",
        "response": (
            "Healthy hair starts from within!\n\n"
            "**Basic Hair Care:**\n"
            "• Wash hair 2-3 times per week (not daily)\n"
            "• Use a mild, sulfate-free shampoo\n"
            "• Always use conditioner on lengths, not roots\n"
            "• Don't rub hair with towel — pat dry gently\n"
            "• Avoid excessive heat styling\n\n"
            "**For Hair Growth & Strength:**\n"
            "• Eat protein-rich foods (eggs, nuts, lentils)\n"
            "• Include iron, zinc, and biotin in your diet\n"
            "• Oil massage once a week (coconut, almond, or castor oil)\n"
            "• Stay hydrated\n"
            "• Manage stress — stress causes hair fall\n\n"
            "**Prevent Hair Fall:**\n"
            "• Don't tie hair too tightly\n"
            "• Avoid chemical treatments\n"
            "• Get 7-8 hours of sleep\n"
            "• Check for iron, vitamin D, and thyroid deficiencies\n\n"
            "If you're experiencing excessive hair fall (100+ strands/day), consult a dermatologist."
        ),
    },
}


# ─── TOPIC KEYWORD MATCHING ─────────────────────────────────────────

FITNESS_KEYWORDS = {
    "weight loss": ["weight loss", "lose weight", "fat loss", "burn fat", "slim down", "reduce weight", "belly fat", "body fat"],
    "weight gain": ["weight gain", "gain weight", "bulk up", "bulking", "put on weight", "skinny", "underweight"],
    "muscle gain": ["muscle", "build muscle", "muscle gain", "muscle building", "abs", "biceps", "six pack", "bodybuilding", "strength training"],
    "workout": ["workout", "work out", "exercise", "gym", "home workout", "training", "cardio", "hiit", "circuit"],
    "yoga": ["yoga", "meditation", "meditate", "flexibility", "mindfulness", "pranayama", "asana"],
    "running": ["running", "jogging", "jog", "run", "marathon", "5k", "sprint", "treadmill"],
    "stretching": ["stretching", "stretch", "mobility", "warm up", "cool down", "stiff", "tight muscles"],
}

NUTRITION_KEYWORDS = {
    "diet plan": ["diet", "diet plan", "meal plan", "eating plan", "calorie", "calories", "what to eat", "food plan", "balanced diet"],
    "protein": ["protein", "whey", "protein shake", "protein powder", "protein sources", "amino acids"],
    "hydration": ["hydration", "water intake", "how much water", "dehydrated", "dehydration", "drink water", "water"],
    "vitamins": ["vitamin", "vitamins", "minerals", "supplements", "supplement", "multivitamin", "vitamin d", "vitamin c", "iron", "zinc", "calcium"],
    "healthy eating": ["healthy food", "healthy eating", "healthy meals", "nutrition", "nutritious", "junk food", "clean eating", "superfoods"],
}

WELLNESS_KEYWORDS = {
    "sleep": ["sleep", "sleeping", "insomnia", "cant sleep", "sleep quality", "sleep better", "wake up", "nap", "rest"],
    "stress": ["stress", "stressed", "overwhelmed", "burnout", "anxious", "tension", "relax", "relaxation", "calm"],
    "energy": ["energy", "energetic", "lethargic", "sluggish", "boost energy", "more energy", "always tired", "low energy"],
    "productivity": ["productivity", "productive", "focus", "concentrate", "concentration", "procrastination", "time management", "discipline", "study", "studying"],
    "mental health": ["mental health", "depression", "sad", "lonely", "hopeless", "therapy", "counseling", "emotional", "mood", "happiness", "self care", "self-care"],
    "morning routine": ["morning routine", "morning habits", "wake up early", "morning", "start the day", "daily routine"],
    "staying active": ["staying active", "stay active", "active lifestyle", "sedentary", "sitting all day", "move more", "keep active", "active in college", "active during"],
    "skin care": ["skin", "skincare", "skin care", "acne", "pimples", "glowing skin", "clear skin", "dark circles", "sunscreen"],
    "hair care": ["hair", "hair care", "haircare", "hair fall", "hair loss", "dandruff", "hair growth", "bald", "balding"],
}


# ─── CONVERSATIONAL RESPONSES ───────────────────────────────────────

GREETINGS = ["hi", "hello", "hey", "hii", "hiii", "good morning", "good afternoon",
             "good evening", "howdy", "sup", "what's up", "whats up", "yo"]

GREETING_RESPONSE = (
    "Hello! 👋 I'm **MedSync AI**, your intelligent assistant.\n\n"
    "I can help you with a wide range of topics:\n"
    "• 🏥 **Health & Wellness** — symptoms, fitness, nutrition, lifestyle\n"
    "• 💻 **Programming & Tech** — coding, AI/ML, web development\n"
    "• 📚 **Education & Learning** — study tips, concepts, explanations\n"
    "• 💼 **Business & Career** — career advice, interview prep, planning\n"
    "• 🔬 **Science & Math** — explanations, problem solving\n"
    "• 💬 **General Knowledge** — any question you have!\n"
    "• 📅 **Appointment Booking** — schedule with a doctor\n\n"
    "**What can I help you with today?** Just ask me anything! 😊"
)

THANK_WORDS = ["thank", "thanks", "thank you", "thx", "ty", "appreciated", "helpful"]

THANK_RESPONSE = (
    "You're welcome! 😊 I'm glad I could help.\n\n"
    "Feel free to ask me anything else — whether it's about health, tech, education, career, or anything on your mind. "
    "I'm here for you!\n\n"
    "Have a great day! 💪"
)

FAREWELL_WORDS = ["bye", "goodbye", "see you", "take care", "gotta go", "later"]

FAREWELL_RESPONSE = (
    "Take care! 👋 It was great chatting with you.\n\n"
    "Come back anytime you have questions — I'm here 24/7 to help with anything! "
    "Wishing you the best! 🌟"
)


# ─── MAIN FALLBACK FUNCTION ─────────────────────────────────────────

def _match_keywords(message_lower, keywords_map):
    """Match message against keyword map. Returns best matching topic key or None."""
    best_match = None
    best_score = 0

    for topic_key, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in message_lower:
                score = len(keyword)  # longer match = more specific
                if score > best_score:
                    best_score = score
                    best_match = topic_key

    return best_match


def _match_symptoms(message_lower):
    """Match message to symptom keys."""
    matched = set()
    for symptom_key in SYMPTOM_DATABASE:
        if symptom_key in message_lower:
            matched.add(symptom_key)
    for alias, symptom_key in SYMPTOM_ALIASES.items():
        if alias in message_lower and symptom_key and symptom_key in SYMPTOM_DATABASE:
            matched.add(symptom_key)
    return list(matched)


def _classify_intent(message_lower):
    """Classify user message intent: greeting, farewell, thanks, fitness, nutrition, wellness, symptom, or unknown."""
    # Check greetings (only if message is short)
    words = message_lower.split()
    if len(words) <= 4:
        for g in GREETINGS:
            if g in message_lower:
                return "greeting", None

    # Check thanks
    for t in THANK_WORDS:
        if t in message_lower:
            return "thanks", None

    # Check farewell
    for f in FAREWELL_WORDS:
        if f in message_lower:
            return "farewell", None

    # Check fitness
    fit_match = _match_keywords(message_lower, FITNESS_KEYWORDS)
    if fit_match:
        return "fitness", fit_match

    # Check nutrition
    nut_match = _match_keywords(message_lower, NUTRITION_KEYWORDS)
    if nut_match:
        return "nutrition", nut_match

    # Check wellness
    well_match = _match_keywords(message_lower, WELLNESS_KEYWORDS)
    if well_match:
        return "wellness", well_match

    # Check symptoms
    symptoms = _match_symptoms(message_lower)
    if symptoms:
        return "symptom", symptoms

    return "unknown", None


def generate_fallback_response(user_message, conversation_history=None):
    """
    Generate an intelligent local response based on message classification.
    Returns (response_text, parsed_data) tuple.
    parsed_data is only populated for symptom-related responses.
    """
    message_lower = user_message.lower().strip()
    intent, data = _classify_intent(message_lower)

    # ── Greeting ──
    if intent == "greeting":
        return GREETING_RESPONSE, None

    # ── Thanks ──
    if intent == "thanks":
        return THANK_RESPONSE, None

    # ── Farewell ──
    if intent == "farewell":
        return FAREWELL_RESPONSE, None

    # ── Fitness ──
    if intent == "fitness":
        topic = FITNESS_TOPICS[data]
        return topic["response"], None

    # ── Nutrition ──
    if intent == "nutrition":
        topic = NUTRITION_TOPICS[data]
        return topic["response"], None

    # ── Wellness ──
    if intent == "wellness":
        topic = WELLNESS_TOPICS[data]
        return topic["response"], None

    # ── Symptoms / Medical ──
    if intent == "symptom":
        matched_symptoms = data
        all_diseases = []
        all_advice = []
        specializations = []
        follow_ups = []

        for symptom in matched_symptoms:
            info = SYMPTOM_DATABASE[symptom]
            all_diseases.extend(info["possible_diseases"])
            all_advice.append(info["basic_advice"])
            specializations.append(info["recommended_specialization"])
            follow_ups.extend(info.get("follow_up_questions", []))

        # Deduplicate diseases
        seen = set()
        unique_diseases = []
        for d in all_diseases:
            if d not in seen:
                seen.add(d)
                unique_diseases.append(d)

        primary_spec = specializations[0] if specializations else "General Medicine"
        confidence = "high" if len(matched_symptoms) >= 3 else ("medium" if len(matched_symptoms) >= 2 else "low")
        symptom_str = ", ".join(matched_symptoms)

        parts = []

        # Check urgency
        urgent = any(SYMPTOM_DATABASE[s].get("basic_advice", "").startswith("⚠️") for s in matched_symptoms)
        if urgent:
            parts.append(
                "⚠️ **IMPORTANT**: Some of your symptoms may require urgent attention. "
                "If this is an emergency, please call your local emergency services immediately.\n"
            )

        parts.append(f"Based on your symptoms ({symptom_str}), here's my assessment:\n")

        parts.append("**Possible Conditions:**")
        for i, disease in enumerate(unique_diseases[:5], 1):
            parts.append(f"  {i}. {disease}")

        parts.append(f"\n**Recommended Specialist:** {primary_spec}")
        parts.append(f"**Confidence Level:** {confidence}\n")

        parts.append("**Advice:**")
        for advice in all_advice[:3]:
            parts.append(f"• {advice}")

        if follow_ups:
            parts.append("\n**To refine my assessment, could you tell me:**")
            for q in follow_ups[:3]:
                parts.append(f"  • {q}")

        parts.append(
            "\n⚠️ **Medical Disclaimer:** This is for informational purposes only. "
            "Please consult a healthcare professional for proper diagnosis and treatment."
        )

        parsed_data = {
            "possible_diseases": unique_diseases[:5],
            "confidence_level": confidence,
            "recommended_specialization": primary_spec,
            "basic_advice": all_advice[0] if all_advice else "Consult a medical professional."
        }

        return "\n".join(parts), parsed_data

    # ── Unknown / General ──
    # For topics we don't have a local database for, provide a helpful response
    # that acknowledges we're a general-purpose assistant
    general_response = (
        f"That's a great question! While I'm currently running in offline mode with limited capabilities, "
        f"I can still help you with many topics.\n\n"
        f"Here's what I can assist with right now:\n\n"
        f"**🏥 Health & Medical:**\n"
        f"  • Describe any symptoms for guidance\n"
        f"  • Ask about specific conditions\n\n"
        f"**🏋️ Fitness & Exercise:**\n"
        f"  • Workout plans, weight loss/gain, yoga, running\n\n"
        f"**🥗 Nutrition & Diet:**\n"
        f"  • Diet plans, protein, vitamins, healthy eating\n\n"
        f"**😴 Lifestyle & Wellness:**\n"
        f"  • Sleep, stress, energy, productivity, skincare\n\n"
        f"**📅 Appointments:**\n"
        f"  • Say \"book an appointment\" to schedule with a doctor\n\n"
        f"For **programming, science, career advice**, and other general topics, "
        f"I work best when the AI service is online. Try rephrasing your question "
        f"or ask me about any of the topics above!\n\n"
        f"Your question: *\"{user_message}\"*"
    )
    return general_response, None
