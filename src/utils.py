from datetime import datetime
import pytz

sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
sao_paulo_time = datetime.now(sao_paulo_tz)
formatted_time = sao_paulo_time.strftime('%Y-%m-%d %H:%M:%S')