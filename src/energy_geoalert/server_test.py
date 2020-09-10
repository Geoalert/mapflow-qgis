# -*- coding: utf-8 -*-
import asyncio

clients = []
soc_emei = {}  # сокет:емей


class SimpleChatClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info("peername")
        print('Подключился: {}'.format(self.peername))
        clients.append(self)

    def data_received(self, data):

        print('{} отправил: {}'.format(self.peername, data.decode()))

        print(self.peername[1])

        # for client in clients:
        #
        #     # обработка сообщения и ответ
        #     data = str(data)
        #     if '#L#' in data:  # Если получаем логин
        #         print('Login')
        #         # добавляем устройство в словарь
        #         soc_emei[self.peername[1]] = data[5:20]
        #
        #         client.transport.write(bytes('#AL#1\r\n', encoding='UTF-8'))  # отвечаем что готовы принять данные
        #     elif '#B#' in data:  # Если получаем данные
        #         print('Black')
        #         print('находим номер сессии', soc_emei[self.peername[1]])
        #
        #         simb_n = str(data.count('|') + 1)
        #         client.transport.write(bytes('#AB#' + simb_n + '\r\n', encoding='UTF-8'))  # подтверждаем что приняли
        #      # сохранение сообщения
        #     print(soc_emei)
            # тут вставляем обработку данных и ответы на сообщения

    def connection_lost(self, ex):
        print('Отключился: {}'.format(self.peername))
        clients.remove(self)
        del soc_emei[self.peername[1]]


# Цикл событий невозможно прервать, если в нём
# не происходят события. Чтобы избежать этого
# регистрируем в цикле фунцию, которая будет
# вызываться раз в секунду.
def wakeup():
    loop = asyncio.get_event_loop()
    loop.call_later(1, wakeup)




if __name__ == '__main__':
    print('Запуск...')

    # Получаем цикл событий
    loop = asyncio.get_event_loop()
    # Регистрируем "отлипатель"
    loop.call_later(1, wakeup)
    # Создаём асинхронную сопрограмму-протокол
    coro = loop.create_server(SimpleChatClientProtocol, host='', port=8001)
    # Регистрируем её в цикле событий на выполнение
    server = loop.run_until_complete(coro)

    for socket in server.sockets:
        print('Сервер запущен на {}'.format(socket.getsockname()))
    print('Выход по Ctrl+C\n')

    try:
        loop.run_forever()  # Запускаем бесконечный цикл событий
    except KeyboardInterrupt:  # Программа прервана нажатием Ctrl+C
        pass
    finally:
        server.close()  # Закрываем протокол
        loop.run_until_complete(server.wait_closed())  # Асинхронно ожидаем окончания закрытия
    loop.close()  # Закрываем цикл событий
