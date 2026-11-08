# -*- coding: utf-8 -*-
"""
Alexa-навык «Копилка воды»: считает выпитые стаканы воды за день.
Задача проекта: голосовой дневник питьевого режима.

Требуется пакет ask-sdk-core (см. requirements.txt).
Счёт хранится в атрибутах сессии, поэтому сбрасывается между сессиями.
Чтобы счёт жил между сессиями, подключите DynamoDB-адаптер (см. README).
"""

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Response

# Максимум за день — чтобы случайные числа не ломали счётчик
MAX_GLASSES = 30

HELP_TEXT = (
    "Это навык «Копилка воды». Скажите: «выпил два стакана», "
    "«сколько я выпил» или «обнули счётчик»."
)


def plural(n: int) -> str:
    """Возвращает слово «стакан» в нужной форме для числа n."""
    n = abs(n) % 100
    if 11 <= n <= 14:
        return "стаканов"
    n %= 10
    if n == 1:
        return "стакан"
    if 2 <= n <= 4:
        return "стакана"
    return "стаканов"


def total_phrase(total: int) -> str:
    if total == 0:
        return "Пока ни одного стакана."
    return f"Сегодня выпито {total} {plural(total)} воды."


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak = "Привет! Я копилка воды. Скажите, сколько стаканов вы выпили, и я запомню."
        handler_input.response_builder.speak(speak).ask("Например: выпил два стакана.")
        return handler_input.response_builder.response


class AddWaterIntentHandler(AbstractRequestHandler):
    """Записывает выпитые стаканы. «Выпил три стакана», «добавь два стакана»."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AddWaterIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        glasses = 1
        if slots.get("glasses") and slots["glasses"].value:
            glasses = int(float(slots["glasses"].value))
        glasses = max(1, min(glasses, MAX_GLASSES))

        attrs = handler_input.attributes_manager.session_attributes
        attrs["total"] = attrs.get("total", 0) + glasses
        total = attrs["total"]

        speak = f"Записала, {glasses} {plural(glasses)}. {total_phrase(total)}"
        handler_input.response_builder.speak(speak).ask("Что-нибудь ещё?")
        return handler_input.response_builder.response


class WaterStatusIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("WaterStatusIntent")(handler_input)

    def handle(self, handler_input):
        attrs = handler_input.attributes_manager.session_attributes
        total = attrs.get("total", 0)
        goal = 8
        if total >= goal:
            speak = f"{total_phrase(total)} Цель восемь стаканов достигнута! Молодцы."
        else:
            speak = (
                f"{total_phrase(total)} До цели в восемь стаканов осталось "
                f"{goal - total} {plural(goal - total)}."
            )
        handler_input.response_builder.speak(speak).ask("Скажите, если выпьете ещё.")
        return handler_input.response_builder.response


class ResetWaterIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ResetWaterIntent")(handler_input)

    def handle(self, handler_input):
        handler_input.attributes_manager.session_attributes["total"] = 0
        handler_input.response_builder.speak(
            "Счётчик обнулён. Начинаем с чистого листа!"
        ).ask("Что-нибудь ещё?")
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        handler_input.response_builder.speak(HELP_TEXT).ask(HELP_TEXT)
        return handler_input.response_builder.response


class CancelAndStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)
            or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input):
        handler_input.response_builder.speak("До встречи!")
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        handler_input.response_builder.speak(
            "Не поняла команду. " + HELP_TEXT
        ).ask(HELP_TEXT)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        print(f"Ошибка: {exception}")
        handler_input.response_builder.speak(
            "Что-то пошло не так. Попробуйте ещё раз."
        ).ask("Повторите команду, пожалуйста.")
        return handler_input.response_builder.response


sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(AddWaterIntentHandler())
sb.add_request_handler(WaterStatusIntentHandler())
sb.add_request_handler(ResetWaterIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
