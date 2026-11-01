import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from openai import APIConnectionError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from config import REQUIRED_ENV_VARS
from chat_service import ChatServiceError, preguntar_rio_claro
from auth_service import crear_principal, crear_principal_publico
from rag_service import KnowledgeDocument


CLIENTE = crear_principal_publico()
OBRERO = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "worker-1",
        "roles": ["obrero"],
    }
)


class AskRioClaroTests(unittest.TestCase):
    def test_sends_question_and_knowledge_context_to_foundry(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        with patch("chat_service.OpenAI") as openai_class:
            openai_class.return_value.responses.create.return_value = SimpleNamespace(
                output_text=json.dumps(
                    {
                        "answer": "Respuesta de prueba",
                        "sources": ["horarios.txt"],
                    }
                )
            )
            with patch.dict(os.environ, environment, clear=True):
                with patch(
                    "chat_service.obtener_documentos",
                    return_value=[
                        KnowledgeDocument("horarios.txt", "Datos aprobados")
                    ],
                ):
                    respuesta = preguntar_rio_claro("¿Cuál es el horario?", CLIENTE)

        self.assertEqual(respuesta.answer, "Respuesta de prueba")
        self.assertEqual(respuesta.sources, ("horarios.txt",))
        request = openai_class.return_value.responses.create.call_args.kwargs
        prompt = request["input"][0]["content"].casefold()
        self.assertIn("asistente de clientes", prompt)
        self.assertIn("no reveles ni infieras información interna", prompt)
        self.assertIn("Datos aprobados", request["input"][1]["content"])
        self.assertIn("¿Cuál es el horario?", request["input"][1]["content"])
        self.assertEqual(
            request["text"]["format"]["schema"]["properties"]["sources"]["items"]["enum"],
            ["horarios.txt"],
        )

    def test_internal_assistant_uses_role_limited_instructions(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        with patch("chat_service.OpenAI") as openai_class:
            openai_class.return_value.responses.create.return_value = SimpleNamespace(
                output_text=json.dumps(
                    {"answer": "Respuesta de prueba", "sources": ["inventario.txt"]}
                )
            )
            with patch.dict(os.environ, environment, clear=True):
                with patch(
                    "chat_service.obtener_documentos",
                    return_value=[
                        KnowledgeDocument("inventario.txt", "Inventario")
                    ],
                ):
                    preguntar_rio_claro("¿Qué hay?", OBRERO)

        request = openai_class.return_value.responses.create.call_args.kwargs
        prompt = request["input"][0]["content"].casefold()
        self.assertIn("asistente interno", prompt)
        self.assertIn("autorizada para el rol", prompt)
        self.assertIn("no inventes existencias", prompt)

    def test_foundry_connection_errors_are_reported_without_service_details(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        with patch("chat_service.OpenAI") as openai_class:
            openai_class.return_value.responses.create.side_effect = APIConnectionError(
                message="private service response",
                request=object(),
            )
            with patch.dict(os.environ, environment, clear=True):
                with patch(
                    "chat_service.obtener_documentos",
                    return_value=[KnowledgeDocument("horarios.txt", "Datos")],
                ):
                    with self.assertRaises(ChatServiceError) as raised:
                        preguntar_rio_claro("Pregunta", CLIENTE)

        self.assertIn("Verifique la conexión", str(raised.exception))
        self.assertNotIn("private service response", str(raised.exception))

    def test_sends_recent_conversation_before_the_current_question(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        previous_messages = [
            {"role": "user", "content": "¿Qué vende Río Claro?"},
            {"role": "assistant", "content": "Productos de limpieza."},
        ]
        with patch("chat_service.OpenAI") as openai_class:
            openai_class.return_value.responses.create.return_value = SimpleNamespace(
                output_text=json.dumps(
                    {
                        "answer": "Tenemos productos de limpieza.",
                        "sources": ["catalogo.txt"],
                    }
                )
            )
            with patch.dict(os.environ, environment, clear=True):
                with patch(
                    "chat_service.obtener_documentos",
                    return_value=[KnowledgeDocument("catalogo.txt", "Catálogo")],
                ):
                    preguntar_rio_claro(
                        "¿Tienen cloro?",
                        CLIENTE,
                        historial=previous_messages,
                    )

        messages = openai_class.return_value.responses.create.call_args.kwargs["input"]
        self.assertEqual(messages[1], previous_messages[0])
        self.assertEqual(messages[2], previous_messages[1])
        self.assertIn("¿Tienen cloro?", messages[3]["content"])

    def test_rejects_citations_outside_the_documents_sent_to_the_model(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        with patch("chat_service.OpenAI") as openai_class:
            openai_class.return_value.responses.create.return_value = SimpleNamespace(
                output_text=json.dumps(
                    {"answer": "Respuesta", "sources": ["inventario.txt"]}
                )
            )
            with patch.dict(os.environ, environment, clear=True):
                with patch(
                    "chat_service.obtener_documentos",
                    return_value=[KnowledgeDocument("horarios.txt", "Horario")],
                ):
                    with self.assertRaisesRegex(
                        ChatServiceError,
                        "documento no disponible",
                    ):
                        preguntar_rio_claro("Pregunta", CLIENTE)

    def test_allows_an_answer_without_documentary_support(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        with patch("chat_service.OpenAI") as openai_class:
            openai_class.return_value.responses.create.return_value = SimpleNamespace(
                output_text=json.dumps(
                    {"answer": "No hay información suficiente.", "sources": []}
                )
            )
            with patch.dict(os.environ, environment, clear=True):
                with patch(
                    "chat_service.obtener_documentos",
                    return_value=[KnowledgeDocument("horarios.txt", "Horario")],
                ):
                    respuesta = preguntar_rio_claro("Pregunta sin respaldo", CLIENTE)

        self.assertEqual(respuesta.sources, ())

    def test_customer_chat_answers_only_matching_synthetic_order_requests(self):
        response = preguntar_rio_claro(
            "¿Cuál es el estado del pedido RC-DEMO-1001 de Ana Lopez?",
            CLIENTE,
        )

        self.assertIn("En preparación", response.answer)
        self.assertIn("sintético", response.answer)
        self.assertEqual(response.sources, ("pedidos_demo.json",))

    def test_customer_chat_does_not_disclose_synthetic_order_without_customer_name(self):
        response = preguntar_rio_claro(
            "¿Cuál es el estado del pedido RC-DEMO-1001?",
            CLIENTE,
        )

        self.assertIn("nombre completo", response.answer)
        self.assertEqual(response.sources, ())

    def test_customer_chat_explains_how_to_request_synthetic_order_tracking(self):
        response = preguntar_rio_claro("¿Cómo va el seguimiento de mi pedido?", CLIENTE)

        self.assertIn("RC-DEMO-0000", response.answer)
        self.assertIn("nombre completo", response.answer)
        self.assertIn("No compartas datos de pedidos reales", response.answer)
        self.assertEqual(response.sources, ())

    def test_customer_chat_intercepts_order_status_inquiry_without_calling_foundry(self):
        with patch("chat_service.OpenAI") as openai_class:
            response = preguntar_rio_claro(
                "¿Tienen información sobre el estado de pedidos?",
                CLIENTE,
            )

        openai_class.assert_not_called()
        self.assertIn("RC-DEMO-0000", response.answer)
        self.assertEqual(response.sources, ())


if __name__ == "__main__":
    unittest.main()
