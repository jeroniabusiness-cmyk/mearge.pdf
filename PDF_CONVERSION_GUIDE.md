# PDF Converter - User Guide

## 🔄 How to Convert Your PDFs

### Quick Start

1. **Start conversion**
   ```
   Send: /convert
   ```

2. **Upload your PDF**
   - Send any PDF file up to 50MB
   - The bot will analyze it for text/images

3. **Choose your format**
   - **📸 Images** (JPG/PNG)
   - **📝 DOCX** (Microsoft Word)
   - **📃 TXT** (Plain Text)

4. **Configure & Download**
   - Select page ranges
   - Choose quality
   - Get your files!

## ✨ Features

### 📸 PDF to Images

- **JPG or PNG** - Choose your preferred format
- **High Quality** - Up to 600 DPI resolution
- **Page Select** - Convert specific pages (e.g., "1-3, 5")
- **ZIP Archive** - Multiple pages are automatically zipped

### 📝 PDF to DOCX (Word)

- **Layout Preserved** - Formatting and images kept intact
- **Editable** - Get a standard Word document
- **Select Pages** - Convert only what you need

### 📃 PDF to Text (TXT)

- **Fast Extraction** - Quickly get raw text
- **Layout Mode** - Try to keep the visual table/text layout
- **Batch Extract** - Handle long documents easily

## 📱 Step-by-Step Guide

### Simple Page Extraction to Images

```
1. /convert
2. Upload: document.pdf
3. Click: "📸 PDF → Images"
4. Click: "📏 Select Pages"
5. Send: 1, 3, 5
6. Click: "✅ Convert Now"
   ⏳ Processing...
   ✅ ZIP file sent!
```

### PDF to Word Document

```
1. /convert
2. Upload: resume.pdf
3. Click: "📝 PDF → DOCX"
   ⏳ Converting...
   ✅ Word file sent!
```

## ⚙️ Advanced Settings

### Page Ranges

Use these formats to select specific pages:
- `all` - Every page
- `1-5` - Range of pages
- `1, 3, 5` - Individual pages
- `1-3, 7, 10-12` - Complex selection

### Image Quality & DPI

- **Low (150 DPI)** - Smallest files, good for mobile
- **Medium (300 DPI)** - Balanced quality (Default)
- **High (600 DPI)** - Best for printing or detailed scans

**Quality:**
- **Low (60%)** - Maximum compression
- **Medium (85%)** - Good balance (Default)
- **High (95%)** - Maximum detail

## 🔧 Troubleshooting

### "No text found"
**Cause:** The PDF is likely a scanned image without an OCR layer.
**Solution:** Use the **PDF → Images** conversion instead.

### "Conversion Failed"
**Cause:** Complex layouts or encrypted PDFs.
**Solution:**
1. Try a smaller page range
2. Ensure the PDF isn't password protected
3. Try a lower DPI setting

### Poppler Error (Server Side)
If you see an error about "poppler", contact the bot administrator to ensure dependencies are installed.

## 📊 Limits

- **Max File Size:** 50MB
- **Max Pages:** Depends on server RAM (usually ~50-100 pages per batch)
- **Timeout:** 30 minutes per session

---

Happy converting! 🔄📄
