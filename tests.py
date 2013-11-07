import unittest
from ubidots.apiclient import ServerBridge
from ubidots.apiclient import try_again
from ubidots.apiclient import raise_informative_exception
from ubidots.apiclient import validate_input
from ubidots.apiclient import UbidotsError400, UbidotsError500, UbidotsInvalidInputError
from mock import patch, MagicMock, Mock
import json


class TestServerBridge(unittest.TestCase):

	def setUp(self):
		self.original_initialize = ServerBridge.initialize
		ServerBridge.initialize = MagicMock()
		apikey = "anyapikey"
		self.serverbridge = ServerBridge(apikey=apikey)
		self.serverbridge._token_header = {'X-AUTH-TOKEN': 'the token'}


	def tearDown(self):
		ServerBridge.initialize = self.original_initialize



	def test_when_ServerBridge_initializes_with_key_it_asks_for_a_token(self):
		with patch('ubidots.apiclient.requests') as mock_request:
			ServerBridge.initialize = self.original_initialize
			apikey = "anyapikey"
			sb = ServerBridge(apikey=apikey)
			mock_request.post.assert_called_once_with(
				"%s%s"%(sb.base_url, "auth/token"),
				headers = {'content-type': 'application/json', 'X-UBIDOTS-APIKEY': 'anyapikey'}
			)

	def test_when_ServerBridge_initializes_with_token_it_set_it_correctly(self):
			sb = ServerBridge(token="anytoken")
			self.assertEqual(sb._token_header, {'X-AUTH-TOKEN': 'anytoken'})



	def test_get_includes_specific_headers(self):

		with patch('ubidots.apiclient.requests') as mock_request:
			self.serverbridge.get("any/path")

			mock_request.get.assert_called_once_with(
				"%s%s"%(self.serverbridge.base_url, "any/path"),
				headers = {'content-type': 'application/json', 'X-AUTH-TOKEN': 'the token'}
			)

	def test_post_includes_specific_headers_and_data(self):

		with patch('ubidots.apiclient.requests') as mock_request:
			data = {"dataone":1, "datatwo":2}
			self.serverbridge.post("any/path", data)

			mock_request.post.assert_called_once_with(
				"%s%s"%(self.serverbridge.base_url, "any/path"),
				headers = {'content-type': 'application/json', 'X-AUTH-TOKEN': 'the token'},
				data = json.dumps(data)
			)

	def test_delete_includes_specific_headers(self):

		with patch('ubidots.apiclient.requests') as mock_request:
			self.serverbridge.delete("any/path")

			mock_request.delete.assert_called_once_with(
				"%s%s"%(self.serverbridge.base_url, "any/path"),
				headers = {'content-type': 'application/json', 'X-AUTH-TOKEN': 'the token'},
			)


class TestDecorators(unittest.TestCase):

	def test_try_again_decorator_number_of_tries_or_fails(self):
		from collections import namedtuple
		error_codes = [401, 403]

		response = namedtuple('response', 'status_code')
		fn = Mock(side_effect = [response(error_codes[0]) for i in range(10)])
		real_decorator = try_again(error_codes, number_of_tries=10)
		
		serverbridge_mock = Mock()
		wrapper = real_decorator(fn)
		wrapper(serverbridge_mock)
		serverbridge_mock.initialize.assert_called_with()

	def test_raise_informative_exception_decorator(self):
		from collections import namedtuple
		error_codes = [400, 500]
		response = namedtuple('response', 'status_code')
		fn = Mock(side_effect = [response(error_codes[0]), response(error_codes[1])])
		real_decorator = raise_informative_exception(error_codes)
		wrapper = real_decorator(fn)
		self.assertRaises(UbidotsError400, wrapper, Mock() )
		self.assertRaises(UbidotsError500, wrapper, Mock() )

	def test_raise_validate_input_decorator_dict(self):
		fn = lambda *args, **kwargs: 911
		real_decorator = validate_input(dict, ["a", "b", "c"])
		wrapper = real_decorator(fn)

		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), [])
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), {})
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), {"a": 1})
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), {"a": 1, "b": 1})
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), {"a": 1, "b": 1, "d": 1})

		self.assertEqual(wrapper(Mock(), {"a": 1, "b": 1, "c": 1}), 911)

	def test_raise_validate_input_decorator_list(self):
		fn = lambda *args, **kwargs: 911
		real_decorator = validate_input(list, ["p", "q"])
		wrapper = real_decorator(fn)

		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), dict)
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), [{}])
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), [{"p"}])
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), [{"p": 1, "q": 1}, []])
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), [{"p": 1, "q": 1}, {}])
		self.assertRaises(UbidotsInvalidInputError, wrapper, Mock(), [{"p": 1, "q": 1}, {"p": 2}])

		self.assertEqual(wrapper(Mock(), [{"p": 1, "q": 1}]), 911)
		self.assertEqual(wrapper(Mock(), [{"p": 1, "q": 1}, {"p": 2, "q": 2}]), 911)

if __name__ == '__main__':
	unittest.main()
