import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

output_dir = r"C:\Users\harin\Documents\aivi_challenge\adversarial_inputs"
os.makedirs(output_dir, exist_ok=True)

img_path = os.path.join(output_dir, "scanned_resume_raster.png")
pdf_path = os.path.join(output_dir, "test1_scanned_image_resume.pdf")

# 1. Create a raster image of a resume
img = Image.new("RGB", (1700, 2200), color=(248, 248, 248))
draw = ImageDraw.Draw(img)

# Draw simulated scanned resume text
lines = [
    ("RAVI KUMAR - SOFTWARE ENGINEER", 50, 40),
    ("Email: ravi.kumar@example.com | Phone: +91 98765 43210", 110, 24),
    ("--------------------------------------------------------------------------------", 150, 20),
    ("PROFESSIONAL SUMMARY", 190, 28),
    ("Full stack developer with 3+ years experience in Python, FastAPI, and PostgreSQL.", 230, 22),
    ("Demonstrated impact in scaling high-throughput REST APIs and database optimization.", 265, 22),
    ("TECHNICAL SKILLS", 320, 28),
    ("Languages: Python, JavaScript, SQL, C++", 360, 22),
    ("Frameworks & Tools: FastAPI, Django, React, Docker, Git, Redis", 395, 22),
    ("Databases: PostgreSQL, MySQL, MongoDB", 430, 22),
    ("WORK EXPERIENCE", 490, 28),
    ("Associate Software Engineer - Tech Solutions Pvt Ltd (2022 - Present)", 530, 24),
    ("- Developed microservices using FastAPI and Celery, reducing task latency by 35%.", 570, 22),
    ("- Maintained PostgreSQL queries and schema migrations for 1M+ active records.", 605, 22),
    ("- Implemented Docker containerization and CI/CD pipelines.", 640, 22),
    ("EDUCATION", 700, 28),
    ("B.Tech in Computer Science and Engineering - Sunrise Institute of Technology", 740, 22),
    ("CGPA: 8.7/10 (Graduated 2022)", 775, 22),
]

for text, y_pos, font_size in lines:
    draw.text((100, y_pos * 2.2), text, fill=(30, 30, 30))

# Save raster image
img.save(img_path, "PNG")

# 2. Embed into PDF as a pure image with NO embedded text layer
c = canvas.Canvas(pdf_path, pagesize=letter)
c.drawImage(img_path, 0, 0, width=letter[0], height=letter[1])
c.save()

print(f"Generated scanned image-only PDF at: {pdf_path}")
print(f"File size: {os.path.getsize(pdf_path)} bytes")

# 3. Verify that standard text extractors extract 0 text
import pypdf
reader = pypdf.PdfReader(pdf_path)
extracted = "".join([page.extract_text() or "" for page in reader.pages])
print(f"PyPDF extracted text length: {len(extracted.strip())} chars (Expected 0 for image-only PDF)")
