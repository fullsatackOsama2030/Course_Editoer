const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const app = express();
const port = 5000;

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public')); // خدمة الملفات الساكنة

// صفحة البداية
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html')); // إرسال نموذج إضافة الدورة
});

// معالجة إضافة الدورة
app.post('/add-course', (req, res) => {
    const title = req.body.title;
    const description = req.body.description;
    const imageUrl = req.body.image_url;
    const courseType = req.body.course_type;

    // إنشاء محتوى الصفحة الخاصة بالدورة
    const coursePageContent = `
        <!DOCTYPE html>
        <html lang="ar">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>${title}</title>
        </head>
        <body>
            <h1>${title}</h1>
            <img src="${imageUrl}" alt="${title}" style="width:100%; border-radius:10px;">
            <h3>وصف الدورة:</h3>
            <p>${description}</p>
            <h3>نوع الدورة:</h3>
            <p>${courseType}</p>
        </body>
        </html>
    `;

    // اسم الملف الخاص بالدورة
    const fileName = `${title.replace(/\s+/g, '-').toLowerCase()}.html`;
    const filePath = path.join(__dirname, 'public', fileName);

    // حفظ الصفحة كملف جديد
    fs.writeFile(filePath, coursePageContent, (err) => {
        if (err) {
            console.error(err);
            return res.status(500).send('خطأ في إنشاء الصفحة');
        }
        // إعادة توجيه المستخدم إلى صفحة الدورة الجديدة
        res.redirect(`/${fileName}`);
    });
});

// بدء الخادم
app.listen(port, () => {
    console.log(`Server is running on http://127.0.0.1:${port}/templates/admin/index`);
});