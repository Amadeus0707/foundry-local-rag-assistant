# Otomatik Test Sonuclari
Sonuc: **13/13 test gecti**

Ayarlar: model `phi-3.5-mini`, embedding `qwen3-embedding-0.6b`, esik 0.45, top_k 5, komsu 1, hibrit agirlik 0.6

| # | Kategori | Soru | Sonuc | Semantik | Grounding | Not |
|---|----------|------|-------|----------|-----------|-----|
| 1 | ANSWERABLE | How many courses can I withdraw from in one semester at most? | GECTI | 0.817 | 0.73 (high) |  |
| 2 | ANSWERABLE | What GPA do I need to be an honor student? | GECTI | 0.702 | 0.94 (high) |  |
| 3 | ANSWERABLE | By when do I need to apply for a leave of absence? | GECTI | 0.696 | 1.00 (high) |  |
| 4 | ANSWERABLE | What is the maximum duration of an undergraduate program? | GECTI | 0.737 | 0.77 (high) |  |
| 5 | ANSWERABLE | What cumulative GPA do I need to graduate? | GECTI | 0.638 | 0.82 (high) |  |
| 6 | ANSWERABLE | How many semesters of leave of absence can I get at most? | GECTI | 0.779 | 0.64 (high) |  |
| 7 | ANSWERABLE | Let's say I took Math 1, but I passed with a DC. Then I took the re... | GECTI | 0.628 | 0.68 (high) |  |
| 8 | ANSWERABLE | Let's say I took Math 1 and passed with a DC. Then I retook it and ... | GECTI | 0.581 | 0.52 (medium) |  |
| 9 | UNANSWERABLE | What is the campus Wi-Fi password? | GECTI | 0.411 | - |  |
| 10 | UNANSWERABLE | What time does the library close? | GECTI | 0.381 | - |  |
| 11 | UNANSWERABLE | Which cafeteria on campus has the best food? | GECTI | 0.339 | - |  |
| 12 | UNANSWERABLE | How much is the annual tuition fee in Turkish Lira? | GECTI | 0.526 | 0.50 (medium) |  |
| 13 | UNANSWERABLE | What is the minimum number of credits I need to take at the beginni... | GECTI | 0.558 | 0.56 (medium) |  |

## Cevap Detaylari

### 1. How many courses can I withdraw from in one semester at most?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 18 (3), ARTICLE 18 (4), ARTICLE 19 (4), ARTICLE 19 (5), ARTICLE 19 (6), ARTICLE 19 (7), ARTICLE 19 (8), ARTICLE 19 (9), ARTICLE 19 (10)  

> According to the provided context in ARTICLE 19 (5), a student may withdraw from a maximum of two courses in a single semester.

### 2. What GPA do I need to be an honor student?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 16 (4), ARTICLE 16 (5), ARTICLE 25 (5), ARTICLE 25 (6), ARTICLE 25 (7), ARTICLE 25 (8), ARTICLE 25 (9), ARTICLE 25 (10), ARTICLE 25 (11)  

> To qualify for honor status at the end of each semester, students enrolled in the relevant undergraduate program must have a semester GPA between 3.00 and 3.49. To achieve high honor status, a semester GPA of 3.50 or higher is required.

### 3. By when do I need to apply for a leave of absence?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 34 (1), ARTICLE 34 (2), ARTICLE 35 (1), ARTICLE 35 (2), ARTICLE 35 (3), ARTICLE 35 (4), ARTICLE 35 (5), ARTICLE 35 (6)  

> You must submit your application for a leave of absence electronically, along with supporting documents, no later than the last business day of the fourth week following the start of classes for the relevant semester. However, if the reason for the leave arises after this date, there is no specified time limit for submitting the application.

### 4. What is the maximum duration of an undergraduate program?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 7 (1), ARTICLE 7 (2), ARTICLE 7 (3), ARTICLE 9 (1), ARTICLE 9 (2), ARTICLE 9 (3), ARTICLE 17 (2), ARTICLE 17 (3), ARTICLE 17 (4)  

> The maximum duration of an undergraduate program at TED University, as per the provided context, is seven years. This includes all semesters spent enrolled or not enrolled in the undergraduate program, starting from the date of initial enrollment, as well as time spent in exchange programs. However, it does not include time spent in the English preparatory program, summer school, or on leave of absence.

### 5. What cumulative GPA do I need to graduate?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 16 (4), ARTICLE 16 (5), ARTICLE 25 (5), ARTICLE 25 (6), ARTICLE 25 (7), ARTICLE 25 (8), ARTICLE 25 (9), ARTICLE 25 (10), ARTICLE 26 (1), ARTICLE 26 (2)  

> To graduate from a bachelor's degree program at TED University, your cumulative GPA must be at least 2.00, as stated in ARTICLE 26 (1)(b).

### 6. How many semesters of leave of absence can I get at most?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 34 (1), ARTICLE 34 (2), ARTICLE 35 (1), ARTICLE 35 (2), ARTICLE 35 (3), ARTICLE 35 (4), ARTICLE 35 (5), ARTICLE 35 (6)  

> According to the provided context, specifically in Article 35 (2), students may be granted a leave of absence for a maximum of four semesters. Each leave should not exceed two semesters, as determined by the relevant administrative board. Therefore, within these guidelines, a student can receive up to a total of four semesters of leave of absence, with the condition that each individual leave period does not exceed two semesters.

### 7. Let's say I took Math 1, but I passed with a DC. Then I took the remedial course but failed with an F. I need to take Math 2 next semester, and Math 1 is a prerequisite for Math 2. In this case, can I take Math 2 next semester, or am I ineligible to take it because I most recently received an F in Math 1?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 13 (9), ARTICLE 13 (10), ARTICLE 13 (11), ARTICLE 13 (12), ARTICLE 19 (7), ARTICLE 19 (8), ARTICLE 19 (9), ARTICLE 25 (9), ARTICLE 25 (10), ARTICLE 25 (11), ARTICLE 27 (1), ARTICLE 27 (2)  

> According to the context provided in ARTICLE 13 (11), students cannot register for courses for which prerequisites have not been met. However, a student who has received a DD or DC grade in a prerequisite course once is considered to have met the prerequisite even if they later retake the course to improve their grade and receive an F.

In your case, you received a DC in Math 1 and then an F in the remedial course for Math 1. This means that you have met the prerequisite for Math 2, even though your most recent grade for Math 1 was an F. Therefore, you should be eligible to take Math 2 next semester, as long as you meet any other specific requirements or conditions set by the University Administrative Board and with the approval of the Higher Education Council.

However, it is always recommended to consult with your academic advisor or the relevant academic committee to clarify your eligibility and any additional steps you may need to take.

### 8. Let's say I took Math 1 and passed with a DC. Then I retook it and got an F. Math 1 is a prerequisite for Math 2. Can I take Math 2?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 13 (9), ARTICLE 13 (10), ARTICLE 13 (11), ARTICLE 13 (12), ARTICLE 15 (4), ARTICLE 15 (5), ARTICLE 25 (9), ARTICLE 25 (10), ARTICLE 25 (11), ARTICLE 27 (1), ARTICLE 27 (2)  

> According to the context provided in ARTICLE 15 (5), to enroll in a course with a prerequisite, a student must have previously earned a grade of DD or P in that prerequisite course at least once. In your case, you initially received a DC in Math 1, which is considered to meet the prerequisite requirement. Therefore, you can enroll in Math 2, as you have met the prerequisite by retaking Math 1 and receiving a grade of DC.

However, it's important to note that this information is based solely on the provided context, and for a comprehensive understanding, it's always best to refer to the actual regulations of the institution.

### 9. What is the campus Wi-Fi password?

**Sonuc:** GECTI  
**Kaynaklar:** no source passed the 0.45 confidence threshold  

> I don't have that information in the provided context.

### 10. What time does the library close?

**Sonuc:** GECTI  
**Kaynaklar:** no source passed the 0.45 confidence threshold  

> I don't have that information in the provided context.

### 11. Which cafeteria on campus has the best food?

**Sonuc:** GECTI  
**Kaynaklar:** no source passed the 0.45 confidence threshold  

> I don't have that information in the provided context.

### 12. How much is the annual tuition fee in Turkish Lira?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 6 (1), ARTICLE 6 (2), ARTICLE 14 (1), ARTICLE 14 (2), ARTICLE 14 (3), ARTICLE 34 (1), ARTICLE 34 (2), ARTICLE 35 (4), ARTICLE 35 (5), ARTICLE 35 (6)  

> I don't have that information in the provided context. The context does not specify the amount of the annual tuition fee in Turkish Lira.

### 13. What is the minimum number of credits I need to take at the beginning of the semester?

**Sonuc:** GECTI  
**Kaynaklar:** ARTICLE 13 (1), ARTICLE 13 (2), ARTICLE 13 (3), ARTICLE 13 (4), ARTICLE 13 (5), ARTICLE 16 (1), ARTICLE 16 (2), ARTICLE 20 (1), ARTICLE 20 (2), ARTICLE 20 (3), ARTICLE 25 (1), ARTICLE 25 (2), ARTICLE 25 (3)  

> The context provided does not specify the exact minimum number of credits required at the beginning of the semester. It mentions that students must register for all required courses and the specified number of elective courses for that semester during the first semester (ARTICLE 14), but it does not give a specific minimum credit value. For this information, you may need to refer to the academic calendar or consult with an academic advisor as suggested in ARTICLE 5 (not provided in your context).
