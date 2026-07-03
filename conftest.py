import os

# Запуск Qt в безголовом режиме для тестов: отключаем отображение окон
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
