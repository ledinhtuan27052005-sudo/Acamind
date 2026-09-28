import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def _send_email(to_email: str, subject: str, html: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        print(f"\n[DEV] ✉  Email to {to_email}: {subject}\n")
        return False
    msg = MIMEMultipart('alternative')
    msg['From'] = f"Acamind <{settings.SMTP_USER}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as srv:
                srv.login(settings.SMTP_USER, settings.SMTP_PASS)
                srv.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as srv:
                srv.ehlo(); srv.starttls(); srv.login(settings.SMTP_USER, settings.SMTP_PASS)
                srv.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def send_enterprise_ticket_to_admin(name: str, email: str, school: str, phone: str, message: str, ticket_id: str) -> bool:
    admin_email = settings.SMTP_USER
    html = f"""
<html><body style="font-family:Arial,sans-serif;background:#f9fafb;padding:24px;">
<div style="max-width:500px;margin:auto;background:white;border-radius:16px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.08);">
  <h2 style="color:#1d4ed8;margin:0 0 16px">📩 Yêu cầu Enterprise mới</h2>
  <table style="width:100%;font-size:14px;border-collapse:collapse;">
    <tr><td style="color:#6b7280;padding:6px 0">Tên</td><td style="font-weight:600">{name}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0">Email</td><td><a href="mailto:{email}">{email}</a></td></tr>
    <tr><td style="color:#6b7280;padding:6px 0">Trường/TC</td><td style="font-weight:600">{school}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0">Điện thoại</td><td>{phone or '—'}</td></tr>
  </table>
  <div style="margin:16px 0;padding:12px;background:#f0f9ff;border-left:4px solid #3b82f6;border-radius:6px;font-size:14px;">{message or '(Không có nội dung)'}</div>
  <p style="font-size:12px;color:#9ca3af;">Ticket ID: {ticket_id} — Xem tại Admin Panel → Enterprise</p>
</div></body></html>"""
    return _send_email(admin_email, f"[Acamind Enterprise] Yêu cầu từ {school}", html)


def send_offer_to_customer(to_email: str, school_name: str, offer_url: str, amount: int, duration_months: int) -> bool:
    amount_fmt = f"{amount:,}".replace(",", ".") + " đ"
    html = f"""
<html><body style="font-family:Arial,sans-serif;background:#fffbeb;padding:24px;">
<div style="max-width:500px;margin:auto;background:white;border-radius:16px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.08);">
  <h2 style="color:#d97706;margin:0 0 8px">🎓 Form thanh toán Enterprise</h2>
  <p style="color:#6b7280;font-size:14px;margin:0 0 20px">Xin chào <strong>{school_name}</strong>,<br>Admin đã tạo form thanh toán cho tổ chức của bạn.</p>
  <div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:12px;padding:16px;margin:16px 0;text-align:center;">
    <p style="margin:0;font-size:24px;font-weight:800;color:#92400e;">{amount_fmt}</p>
    <p style="margin:4px 0 0;font-size:13px;color:#78350f;">{duration_months} tháng</p>
  </div>
  <div style="text-align:center;margin:20px 0;">
    <a href="{offer_url}" style="display:inline-block;background:#f59e0b;color:white;padding:12px 28px;border-radius:10px;font-weight:700;text-decoration:none;font-size:15px;">Mở form & quét QR thanh toán</a>
  </div>
  <p style="font-size:12px;color:#9ca3af;text-align:center;">Truy cập link trên để điền thông tin và thanh toán.</p>
</div></body></html>"""
    return _send_email(to_email, f"[Acamind] Form thanh toán Enterprise – {school_name}", html)


def send_otp_email(to_email: str, otp: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        print(f"\n[DEV] ✉  OTP for {to_email}: {otp}\n")
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Acamind <{settings.SMTP_USER}>"
    msg['To'] = to_email
    msg['Subject'] = f"[Acamind] Mã xác thực: {otp}"

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f0f2ff;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="480" cellpadding="0" cellspacing="0" style="background:white;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(99,102,241,.12);">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);padding:28px 32px;text-align:center;">
            <p style="margin:0;color:white;font-size:22px;font-weight:800;letter-spacing:-.5px;">Acamind</p>
            <p style="margin:6px 0 0;color:rgba(255,255,255,.75);font-size:13px;">Hệ thống học thuật thông minh</p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 32px;">
            <p style="margin:0 0 8px;color:#111827;font-size:16px;font-weight:600;">Xác thực tài khoản</p>
            <p style="margin:0 0 28px;color:#6b7280;font-size:14px;line-height:1.6;">
              Nhập mã OTP bên dưới để hoàn tất đăng ký. Mã có hiệu lực trong <strong>10 phút</strong>.
            </p>
            <!-- OTP box -->
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center" style="background:#f5f3ff;border:2px dashed #a5b4fc;border-radius:16px;padding:28px;">
                  <span style="font-size:42px;font-weight:900;letter-spacing:16px;color:#4F46E5;">{otp}</span>
                </td>
              </tr>
            </table>
            <p style="margin:24px 0 0;color:#9ca3af;font-size:12px;text-align:center;">
              Không chia sẻ mã này với ai. Nếu bạn không yêu cầu, hãy bỏ qua email này.
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f9fafb;padding:16px 32px;text-align:center;border-top:1px solid #f3f4f6;">
            <p style="margin:0;color:#d1d5db;font-size:11px;">© 2025 Acamind — Academic RAG System</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    msg.attach(MIMEText(html, 'html'))

    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as srv:
                srv.login(settings.SMTP_USER, settings.SMTP_PASS)
                srv.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as srv:
                srv.ehlo()
                srv.starttls()
                srv.login(settings.SMTP_USER, settings.SMTP_PASS)
                srv.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
