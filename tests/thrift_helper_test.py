import mock

from pyramid_zipkin import thrift_helper


@mock.patch('pyramid_zipkin.thrift_helper.zipkin_core.Span', autospec=True)
def test_create_span(Span):
    # Not much logic here so this is just a smoke test. The only
    # substantive thing is that hex IDs get converted to ints.
    thrift_helper.create_span(
        span_id='0x1',
        parent_span_id='0x2',
        trace_id='0xf',
        span_name='foo',
        annotations='ann',
        binary_annotations='binary_ann',
    )
    Span.assert_called_once_with(**{
        'id': 1, 'parent_id': 2,
        'name': 'foo', 'trace_id': 15,
        'name': 'foo', 'annotations': 'ann',
        'binary_annotations': 'binary_ann',
    })


@mock.patch('socket.gethostbyname', autospec=True)
def test_create_endpoint_creates_correct_endpoint(gethostbyname, request):
    gethostbyname.return_value = '0.0.0.0'
    request.registry.settings = {'service_name': 'foo'}
    request.server_port = 8080
    endpoint = thrift_helper.create_endpoint(request)
    assert endpoint.service_name == 'foo'
    assert endpoint.port == 8080
    # An IP address of 0.0.0.0 unpacks to just 0
    assert endpoint.ipv4 == 0


@mock.patch('socket.gethostbyname', autospec=True)
def test_copy_endpoint_with_new_service_name(gethostbyname, request):
    gethostbyname.return_value = '0.0.0.0'
    request.registry.settings = {'service_name': 'foo'}
    request.server_port = 8080
    endpoint = thrift_helper.create_endpoint(request)
    new_endpoint = thrift_helper.copy_endpoint_with_new_service_name(
            endpoint, 'blargh')
    assert new_endpoint.port == 8080
    assert new_endpoint.service_name == 'blargh'
    # An IP address of 0.0.0.0 unpacks to just 0
    assert endpoint.ipv4 == 0


def test_get_id_with_empty_string():
    assert thrift_helper.get_id('') == 0


def test_get_id_with_number():
    assert thrift_helper.get_id('42') == int('42', 16)


def test_create_annotation():
    ann = thrift_helper.create_annotation('foo', 'bar', 'baz')
    assert ('foo', 'bar', 'baz') == (ann.timestamp, ann.value, ann.host)


@mock.patch('pyramid_zipkin.thrift_helper.create_annotation', autospec=True)
def test_annotation_list_builder(ann_mock):
    ann_list = {'foo': 1, 'bar': 2}
    thrift_helper.annotation_list_builder(ann_list, 'host')
    ann_mock.assert_any_call(1000000, 'foo', 'host')
    ann_mock.assert_any_call(2000000, 'bar', 'host')
    assert ann_mock.call_count == 2


def test_create_binary_annotation():
    bann = thrift_helper.create_binary_annotation(
        'foo', 'bar', 'baz', 'bla')
    assert ('foo', 'bar', 'baz', 'bla') == (
        bann.key, bann.value, bann.annotation_type, bann.host)


@mock.patch('pyramid_zipkin.thrift_helper.create_binary_annotation',
            autospec=True)
def test_binary_annotation_list_builder(bann_mock):
    bann_list = {'key1': 'val1', 'key2': 'val2'}
    thrift_helper.binary_annotation_list_builder(bann_list, 'host')
    bann_mock.assert_any_call('key1', 'val1', 6, 'host')
    bann_mock.assert_any_call('key2', 'val2', 6, 'host')
    assert bann_mock.call_count == 2
