# PDF Merge - User Guide

## How to Merge PDFs

### Method 1: Interactive (Recommended)

1. **Start the bot**
   ```
   Send: /start
   ```

2. **Send PDF files**
   - Send your first PDF
   - Send your second PDF
   - Send more PDFs (up to 20)

3. **Merge**
   - Click "🔄 Merge PDFs" button
   - Wait for processing
   - Download your merged PDF!

### Method 2: Commands

1. **Upload files**
   ```
   Send PDF files one by one
   ```

2. **Check uploaded files**
   ```
   Send: /list
   ```

3. **Merge files**
   ```
   Send: /merge
   ```

4. **Download result**
   - Bot will send you the merged PDF

## Features

### ✅ What You Can Do

- Merge 2-20 PDF files
- Files merged in order sent
- See file count and page count
- Automatic compression
- View estimated output size
- Clear session anytime

### 📊 Information Shown

For each PDF:
- File name
- Number of pages
- File size

For merge:
- Total files
- Total pages
- Total input size
- Output size
- Compression ratio

## Commands Reference

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/merge` | Merge uploaded PDFs |
| `/list` | Show uploaded files |
| `/clear` | Clear current session |
| `/stats` | Your statistics |
| `/cancel` | Cancel operation |

## Buttons

### During Upload

- **🔄 Merge PDFs** - Start merging
- **📋 View List** - Show all files
- **🗑️ Clear All** - Remove all files
- **❌ Cancel** - Cancel operation

### After Merge

- **🔄 Merge More PDFs** - Start new merge
- **📊 View Stats** - See your statistics
- **« Main Menu** - Return to menu

## Limits

- **Maximum file size:** 50MB per file
- **Maximum files:** 20 per session
- **Session timeout:** 30 minutes
- **Supported format:** PDF only

## Tips

💡 **Best Practices:**
- Send smaller files first for faster processing
- Check file list before merging
- Files are merged in send order
- Output is usually smaller than total input

⚠️ **Common Issues:**
- Password-protected PDFs not supported
- Corrupted PDFs will be rejected
- Empty PDFs cannot be merged

## Examples

### Example 1: Merge 2 Documents

```
1. Send: document1.pdf
   ✅ PDF Added (10 pages)

2. Send: document2.pdf
   ✅ PDF Added (15 pages)

3. Click: "Merge PDFs"
   ⏳ Merging...
   ✅ Success! (25 pages)
```

### Example 2: Merge Multiple Files

```
1. Send 5 PDF files
2. Use /list to verify
3. Use /merge or click button
4. Download merged PDF
```

## Troubleshooting

**Problem: "File too large"**
- Solution: File must be under 50MB

**Problem: "Need at least 2 files"**
- Solution: Send more PDF files

**Problem: "Invalid PDF"**
- Solution: File may be corrupted or password-protected

**Problem: "Session expired"**
- Solution: Send files again

## Privacy

- Files are temporary (deleted after 24h)
- Session cleared after merge
- No files stored permanently
- Use /cancel to clear immediately

## Support

Having issues?
- Check /help command
- View this guide
- Contact support

---

Enjoy merging PDFs! 📄✨
