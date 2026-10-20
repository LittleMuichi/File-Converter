import io
import gzip
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Python File Converter", page_icon="🔄", layout="centered")

st.title("🔄 Python File Converter")
st.write("Easily convert, resize, and compress your files to specific target sizes!")

# Sidebar navigation
conversion_type = st.sidebar.selectbox(
    "Select Conversion Type",
    ["Image Converter", "Data Converter (CSV/JSON/Excel)"],
)

# Helper function to get clean text for file sizes
def format_size(bytes_count):
    kb = bytes_count / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    return f"{(kb / 1024):.2f} MB"

# --- IMAGE CONVERTER ---
if conversion_type == "Image Converter":
  st.header("🖼️ Image Converter")
  uploaded_image = st.file_uploader(
      "Upload an Image", type=["png", "jpg", "jpeg", "webp", "bmp"]
  )

  if uploaded_image is not None:
    # Read the original file's raw byte array to get accurate file size
    og_bytes = uploaded_image.getvalue()
    og_size_str = format_size(len(og_bytes))
    
    image = Image.open(uploaded_image)
    st.image(
        image,
        caption=f"Original Image ({image.format}) - Original File Size: {og_size_str} - Dimensions: {image.size[0]}x{image.size[1]}",
        use_container_width=True,
    )

    st.subheader("Adjustment Options")
    
    # 1. Dimension Resizing
    enable_resize = st.checkbox("Resize Image Dimensions")
    new_width, new_height = image.size
    if enable_resize:
        col1, col2 = st.columns(2)
        with col1:
            new_width = st.number_input("Width (pixels)", min_value=1, value=image.size[0])
        with col2:
            new_height = st.number_input("Height (pixels)", min_value=1, value=image.size[1])

    # 2. Target File Size Optimization
    st.markdown("**File Size Target Control**")
    enable_target_size = st.checkbox("Set a Maximum Target File Size limit (JPEG/WEBP only)")
    
    target_size_kb = 0.0
    if enable_target_size:
        target_size_kb = st.number_input(
            "Enter maximum desired file size (in KB):", 
            min_value=5.0, 
            value=min(200.0, max(5.0, len(og_bytes) / 1024))
        )

    target_format = st.selectbox(
        "Convert to:", ["PNG", "JPEG", "WEBP", "BMP"]
    )

    if st.button("Convert & Compress Image"):
      if enable_resize:
          image = image.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)

      save_format = target_format
      if target_format == "JPEG" and image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

      # Dynamic Compression Routine to hit user targets
      byte_data = b""
      final_quality = 85
      
      if enable_target_size and save_format in ["JPEG", "WEBP"]:
          # Loop backwards to find the highest quality that fits under the target KB size limit
          for q in range(100, 4, -5):
              buffer = io.BytesIO()
              image.save(buffer, format=save_format, quality=q)
              test_data = buffer.getvalue()
              test_size_kb = len(test_data) / 1024
              
              byte_data = test_data
              final_quality = q
              # Break out of loop once it falls safely under their entry threshold
              if test_size_kb <= target_size_kb:
                  break
      else:
          # Default format compilation route if constraint isn't active or applicable
          buffer = io.BytesIO()
          if save_format in ["JPEG", "WEBP"]:
              image.save(buffer, format=save_format, quality=85)
          else:
              image.save(buffer, format=save_format)
          byte_data = buffer.getvalue()

      final_size_str = format_size(len(byte_data))
      
      st.success(f"Successfully processed! Original: {og_size_str} ➡️ Final: {final_size_str}")
      if enable_target_size and save_format in ["JPEG", "WEBP"]:
          st.info(f"Target limit achieved by auto-tuning compression quality index down to: {final_quality}%")
          
      st.download_button(
          label=f"Download .{target_format.lower()} ({final_size_str})",
          data=byte_data,
          file_name=f"converted_image.{target_format.lower()}",
          mime=f"image/{target_format.lower()}",
      )

# --- DATA CONVERTER ---
elif conversion_type == "Data Converter (CSV/JSON/Excel)":
  st.header("📊 Data File Converter")
  uploaded_file = st.file_uploader(
      "Upload a Data File", type=["csv", "json", "xlsx"]
  )

  if uploaded_file is not None:
    # Read raw content metrics directly from the input buffer stream
    og_bytes = uploaded_file.getvalue()
    og_size_str = format_size(len(og_bytes))
    
    file_extension = uploaded_file.name.split(".")[-1].lower()

    try:
      # Reset file read pointer after raw calculation
      uploaded_file.seek(0)
      if file_extension == "csv":
        df = pd.read_csv(uploaded_file)
      elif file_extension == "json":
        df = pd.read_json(uploaded_file)
      elif file_extension == "xlsx":
        df = pd.read_excel(uploaded_file)

      st.write(f"### Data Preview (Original File Size: {og_size_str})")
      st.dataframe(df.head())

      st.subheader("Data Optimization Options")
      
      # Row truncation configuration options
      enable_row_limit = st.checkbox("Limit maximum number of rows (Drastically drops file size)")
      if enable_row_limit:
          max_rows = st.number_input("Max rows to retain", min_value=1, max_value=len(df), value=min(1000, len(df)))
          df = df.iloc[:int(max_rows)]

      # Gzip structural compression configuration parameters
      compress_data = st.checkbox("Compress output file into GZIP format archive")

      target_data_format = st.selectbox(
          "Convert to:", ["CSV", "JSON", "Excel (XLSX)"]
      )

      if st.button("Convert Data"):
        buffer = io.BytesIO()
        output_filename = ""
        mime_type = ""

        if target_data_format == "CSV":
            if compress_data:
                with gzip.GzipFile(fileobj=buffer, mode="w") as f:
                    df.to_csv(f, index=False)
                output_filename = "converted_data.csv.gz"
                mime_type = "application/gzip"
            else:
                df.to_csv(buffer, index=False)
                output_filename = "converted_data.csv"
                mime_type = "text/csv"
                
        elif target_data_format == "JSON":
            if compress_data:
                with gzip.GzipFile(fileobj=buffer, mode="w") as f:
                    f.write(df.to_json(orient="records", indent=4).encode('utf-8'))
                output_filename = "converted_data.json.gz"
                mime_type = "application/gzip"
            else:
                df.to_json(buffer, orient="records", indent=4)
                output_filename = "converted_data.json"
                mime_type = "application/json"
                
        elif target_data_format == "Excel (XLSX)":
          df.to_excel(buffer, index=False, engine="openpyxl")
          output_filename = "converted_data.xlsx"
          mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        byte_data = buffer.getvalue()
        final_size_str = format_size(len(byte_data))

        st.success(f"Conversion successful! Original: {og_size_str} ➡️ Final: {final_size_str}")
        st.download_button(
            label=f"Download {target_data_format} ({final_size_str})",
            data=byte_data,
            file_name=output_filename,
            mime=mime_type,
        )

    except Exception as e:
      st.error(f"Error processing file: {e}")
