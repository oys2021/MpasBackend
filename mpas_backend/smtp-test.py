# import smtplib
# import socket

# def test_smtp():
#     targets = [
#         ("smtp.gmail.com", 587),
#         ("aspmx.l.google.com", 25),
#         ("alt1.gmail-smtp-in.l.google.com", 25),
#         ("192.168.43.192", 587)  
#     ]
    
#     for host, port in targets:
#         try:
#             print(f"Testing {host}:{port}...")
#             with socket.create_connection((host, port), timeout=15) as sock:
#                 print(f"✅ TCP Connection successful to {host}:{port}")
            
#             if port == 465:
#                 server = smtplib.SMTP_SSL(host, port, timeout=15)
#             else:
#                 server = smtplib.SMTP(host, port, timeout=15)
#                 if port == 587: server.starttls()
                
#             server.ehlo()
#             print("✅ SMTP Handshake successful")
#             server.login("you@gmail.com", "YOUR_APP_PASSWORD")  # USE APP PASSWORD!
#             print("🔥 Login successful! Problem is in Django config")
#             return True
#         except Exception as e:
#             print(f"❌ Failed on {host}:{port} - {type(e).__name__}: {e}")
    
#     print("All connections failed. See error patterns above.")
#     return False

# test_smtp()


import smtplib
try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
        server.starttls()
        server.login("nysagashiwanga@gmail.com", "hdtxhxjaugpjocxn")  
        print("Success!")
except Exception as e:
    print(f"Failed: {e}")