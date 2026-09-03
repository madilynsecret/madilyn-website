วางไฟล์ PDF ที่แจกฟรีในโฟลเดอร์นี้ แล้วแก้ href ในหน้า academy.html

ตัวอย่าง
  downloads/import-checklist.pdf
  downloads/glossary-th-en.pdf
  downloads/incoterms-2020.pdf

ใน academy.html ค้นคำว่า  href="#"  จะเจอปุ่มดาวน์โหลด 3 ปุ่ม
เปลี่ยนเป็น  href="downloads/import-checklist.pdf"  ตามชื่อไฟล์จริง
เพิ่ม download ต่อท้ายถ้าอยากให้เบราว์เซอร์บันทึกไฟล์แทนการเปิด เช่น
  <a class="btn btn-teal btn-block" href="downloads/import-checklist.pdf" download>
