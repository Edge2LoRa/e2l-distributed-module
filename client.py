import rpyc

connection = rpyc.connect('localhost', 18861)

remote_service = connection.root
print(remote_service.new_data({'a': 1, 'b': 2}))
print(remote_service.new_data({'a': 3, 'b': 4}))
print(remote_service.new_data({'a': 5, 'b': 6}))
print(remote_service.new_data({'a': 7, 'b': 28}))


