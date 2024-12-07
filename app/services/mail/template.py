def html_content(reset_link: str):
    return f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}

        .container {{
            background-color: #ffffff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin: auto;
        }}

        h2 {{
            color: #333;
        }}

        p {{
            color: #555;
            line-height: 1.5;
        }}

        a {{
            background-color: green;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 5px;
        }}

        a:hover {{
            background-color: rgb(1, 82, 1);
        }}

        .footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #888;
            text-align: center;
        }}
    </style>
</head>

<body>
    <div class="container">
        <h2>Password Reset Request</h2>
        <p>To reset your password, click the link below:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <div class="footer">
            <p>Thanks,</p>
            <p>The SSI Mart Team</p>
        </div>
    </div>
</body>

</html>
""".strip()