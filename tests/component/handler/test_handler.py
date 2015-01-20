import asyncio
import unittest
from importlib import import_module
from unittest.mock import Mock, patch
component = import_module('interest.handler.handler')


class HandlerTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.args = ('arg1',)
        self.kwargs = {'kwarg1': 'kwarg1'}
        self.service = Mock()
        self.handler = component.Handler(self.service)

    # Tests

    def test_service(self):
        self.assertEqual(self.handler.service, self.service)

    def test_fork(self):
        fork = self.handler.fork()
        self.assertEqual(type(self.handler), type(fork))
        self.assertEqual(self.service, fork.service)

    @patch.object(component, 'Request')
    def test_handle_request(self, Request):
        c = asyncio.coroutine
        match = Mock()
        response = Mock()
        response.write_eof = c(lambda: None)
        match.route.handler = c(lambda req: req)
        self.handler.log_access = Mock()
        self.service.loop.time.return_value = 10
        self.service.dispatcher.resolve = c(lambda req: match)
        self.service.processor.process_request = c(lambda req: req)
        self.service.processor.process_result = c(lambda req, res: response)
        self.service.processor.process_response = c(lambda req, res: res)
        self.service.processor.process_exception = c(lambda req, ex: ex)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.handler.handle_request('message', 'payload'))
        # Check Request call
        Request.assert_called_with(
            None, 'message', 'payload',
            self.handler.transport, self.handler.reader, self.handler.writer)
        # Check log_access call
        self.handler.log_access.assert_called_with(
            'message', None, response.start.return_value, 0)

    @patch.object(component, 'Interaction')
    def test_log_access(self, Interaction):
        self.handler.log_access('message', 'environ', 'response', 'time')
        # Check Interaction call
        Interaction.assert_called_with(
            request='message', response='response',
            transport=self.handler.transport, duration='time')
        # Check service.logger call
        self.service.logger.access.assert_called_with(
            Interaction.return_value)

    @patch.object(component, 'traceback')
    @patch.object(component, 'Interaction')
    def test_log_access_with_error(self, Interaction, traceback):
        Interaction.side_effect = RuntimeError()
        self.handler.log_access('message', 'environ', 'response', 'time')
        # Check service.logger call
        self.service.logger.error.assert_called_with(
            traceback.format_exc.return_value)

    def test_log_debug(self):
        self.handler.log_debug('message', *self.args, **self.kwargs)
        # Check service.logger call
        self.service.logger.debug.assert_called_with(
            'message', *self.args, **self.kwargs)

    def test_log_exception(self):
        self.handler.log_exception('message', *self.args, **self.kwargs)
        # Check service.logger call
        self.service.logger.exception.assert_called_with(
            'message', *self.args, **self.kwargs)
