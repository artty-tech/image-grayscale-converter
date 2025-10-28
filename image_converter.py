import streamlit as st
from PIL import Image
import io
import zipfile

# -----------------------------------------------------------------
# ฟังก์ชันหลักสำหรับการประมวลผลภาพ (ใช้สำหรับ Preview และ Final Output)
# -----------------------------------------------------------------
def process_image(input_data, grayscale_level, is_preview=False):
    """
    อ่านไฟล์/ข้อมูลภาพ, แปลงเป็น Grayscale 100%, และผสม (Blend) กับภาพต้นฉบับ
    """
    try:
        # 1. เปิดภาพต้นฉบับและแปลงเป็นโหมดสี (RGB)
        # ถ้าเป็น Preview เราจะรับ Input เป็น BytesIO (จาก st.file_uploader)
        if is_preview:
            input_data.seek(0) # กลับไปที่ต้นไฟล์ก่อนเปิด
            original_image = Image.open(input_data).convert("RGB")
            # สำหรับ Preview เราไม่ต้องตั้งชื่อไฟล์
            output_filename = None
        else:
            # สำหรับ Final Output เราจะรับ Input เป็น Streamlit UploadedFile
            original_image = Image.open(input_data).convert("RGB")
            file_name, file_ext = input_data.name.rsplit('.', 1)
            output_filename = f"{file_name}_G{grayscale_level}.PNG" # เปลี่ยนเป็น PNG เพื่อคุณภาพที่ดี

        # 2. แปลงภาพต้นฉบับให้เป็น Grayscale 100%
        grayscale_image = original_image.convert("L").convert("RGB")
        
        # 3. กำหนดอัตราส่วนการผสม (Alpha)
        alpha = grayscale_level / 100.0 

        # 4. ผสมภาพ (Blend)
        processed_image = Image.blend(original_image, grayscale_image, alpha)
        
        # 5. จัดการ Output
        if is_preview:
            # สำหรับ Preview ให้คืนค่าเป็นวัตถุ Image
            return processed_image
        else:
            # สำหรับ Final Output ให้คืนค่าเป็นชื่อไฟล์และข้อมูลไบต์
            img_byte_arr = io.BytesIO()
            processed_image.save(img_byte_arr, format='PNG') 
            img_byte_arr.seek(0)
            return output_filename, img_byte_arr.read()
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
        return None, None

# -----------------------------------------------------------------
# ฟังก์ชันสำหรับเคลียร์ไฟล์
# -----------------------------------------------------------------
def clear_files():
    """รีเซ็ตตัวแปรใน Session State เพื่อเคลียร์ไฟล์ที่อัปโหลด"""
    if 'file_uploader_key' not in st.session_state:
        st.session_state['file_uploader_key'] = 0
    
    # เพิ่มค่า Key เพื่อให้ Streamlit สร้าง File Uploader ตัวใหม่
    st.session_state['file_uploader_key'] += 1
    st.info("🖼️ รูปภาพทั้งหมดถูกล้างแล้ว กรุณาอัปโหลดไฟล์ใหม่")


# -----------------------------------------------------------------
# ส่วนติดต่อผู้ใช้ (Streamlit UI)
# -----------------------------------------------------------------
st.set_page_config(page_title="Image Grayscale & Zip Tool", layout="centered")

st.title("🖼️ เครื่องมือแปลงภาพเป็น Grayscale แบบปรับระดับได้")
st.markdown("อัปโหลดหลายภาพ, แปลงเป็น Grayscale, และส่งออกเป็นไฟล์ ZIP By. อาร์ตี้ พม.")

# ต้องเริ่มต้นค่า key ถ้ายังไม่มี
if 'file_uploader_key' not in st.session_state:
    st.session_state['file_uploader_key'] = 0

# 1. แถบปรับระดับ Grayscale
grayscale_level = st.slider(
    "**เลือกระดับความเข้ม Grayscale (0% = สีปกติ, 100% = เทาล้วน)**",
    0, 100, 100, step=1
)
st.info(f"ระดับความเข้ม Grayscale ปัจจุบัน: **{grayscale_level}%**")

# 2. ส่วนอัปโหลดไฟล์ และปุ่มเคลียร์
uploaded_files = st.file_uploader(
    "**อัปโหลดไฟล์ภาพหลายไฟล์**",
    type=['png', 'jpg', 'jpeg'],
    accept_multiple_files=True,
    key=st.session_state['file_uploader_key'] 
)
st.button("🗑️ ล้างรูปภาพและเริ่มใหม่", on_click=clear_files)

# --- ส่วนแสดงผล Preview ---
if uploaded_files:
    # 3. สร้าง Preview (แสดงเฉพาะภาพแรกที่อัปโหลด)
    st.subheader("👀 ตัวอย่างการแสดงผล (จากภาพแรก)")
    st.markdown("ปรับระดับความเข้ม จากแถบด้านบนได้")
    
    # อ่านข้อมูลของภาพแรกในรูปแบบ BytesIO สำหรับ Preview
    first_file = uploaded_files[0]
    # **สำคัญ:** ต้องสร้างสำเนา BytesIO เพื่อไม่ให้รบกวนข้อมูลไฟล์ต้นฉบับ
    file_bytes = io.BytesIO(first_file.getvalue()) 
    
    # ประมวลผลภาพตัวอย่าง
    preview_image = process_image(file_bytes, grayscale_level, is_preview=True)
    
    # แสดงภาพ
    if preview_image:
        st.image(preview_image, caption=f"Preview: Grayscale {grayscale_level}%", use_container_width=True)

# --- ส่วนประมวลผล Final Output ---
if uploaded_files:
    if st.button("🚀 เริ่มการประมวลผลและสร้าง ZIP"):
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            st.text("กำลังประมวลผลภาพทั้งหมด...")
            progress_bar = st.progress(0)
            
            for i, file in enumerate(uploaded_files):
                # ส่งไฟล์ Streamlit UploadedFile ไปประมวลผล
                filename, file_data = process_image(file, grayscale_level, is_preview=False)
                
                if file_data:
                    zf.writestr(filename, file_data)
                
                progress_bar.progress((i + 1) / len(uploaded_files))
        
        st.success(f"✅ ประมวลผลเสร็จสิ้น! สร้างไฟล์ ZIP ที่มี {len(uploaded_files)} ภาพ")
        
        # 4. ปุ่มดาวน์โหลด
        st.download_button(
            label="⬇️ ดาวน์โหลดไฟล์ ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"Grayscale_Level_{grayscale_level}_Images.zip",
            mime="application/zip"
        )
else:
    st.warning("กรุณาอัปโหลดไฟล์ภาพเพื่อเริ่มการทำงาน")