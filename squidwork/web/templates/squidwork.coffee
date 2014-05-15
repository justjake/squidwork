###
# Squidwork in Coffeescript
# class Squidwork handles interaction with a JSON backend
# class Origin manages both Routes and Origin stuff
# time and message data remain in JSON wire format
###
PREFIX = /^all\/?/

class Origin
  constructor: (str) ->
    [route, @host] = str.split('@')
    @path = route.replace(PREFIX, '')

  toString: () ->
    "all/#{@path}@#{@host}"


class Subscription
  constructor: (@parent, @path, @fn) ->
  unsubscribe: () ->
    @parent.remove(@path)


class HandlerList
  constructor: (@debug=false) ->
    # kept sorted by length for fast filtering
    # from shortest to longest
    @handlers = []

    # easily tell if we just need to do a replace
    # maps from path --> index in @handlers
    @exactPaths = {}

  # resort all the handlers
  resort: () ->
    @handlers.sort((a, b) -> return a.path.length - b.path.length)

  # add a handler for a path
  add: (path, fn) ->
    if @exactPaths[path]?
      @exactPaths[path].fn = fn
      return

    # the handler
    h = new Subscription(this, path, fn)

    # store in exact lookup path
    @exactPaths[path] = h
    # store in list
    @handlers.push(h)
    @resort()

    return h

  remove: (path) ->
    if not @exactPaths[path]?
      console.log("SQUIDWORK: skipping null subscription callback for", path)
      return

    h = @exactPaths[path]
    idx = @handlers.indexOf(h)
    if idx == -1
      console.log("SQUIDWORK: could not find handler in list:", h, @handlers)
      return
    @handlers.splice(idx, 1)

  # get the most specific handler for the given path
  for: (path) ->
    path = path.replace(PREFIX, '')

    idx = @handlers.length - 1

    while idx > -1
      cur = @handlers[idx]
      idx -= 1
      if path.indexOf(cur.path) == 0
        # match
        return cur

"""
Subscribe and unsubscrite from squidwork event messages
"""
class Squidwork
  constructor: (@uri, @debug=false) ->
    @handlers = new HandlerList(@debug)
    @_buffer = []  # stores messages that wait for things to open
    @socket = new WebSocket(@uri)
    @socket.onmessage = @recieve_message
    @socket.onopen = @_unbuffer

  parse_time: (str) ->
    [iso, psec] = str.split('.')
    return new Date(iso)

  recieve_message: (event) =>
    """
    run on incoming messages from the websocket bridge.
    parses the event's data field as JSON, than performs dispatch:
    - {success: msg} and {error: msg} are both handled here,
      and are not passed along to user-level handlers
    - Squidwork messages {content, time, origin} passed to most specific
      subscription handler
    """

    if @debug
      console.log("SQUIDWORK: raw data:", event.data)

    data = JSON.parse(event.data)

    if data.error?
      console.log("SQUIDWORK: error:", data.error)
      return

    if data.success?
      console.log("SQUIDWORK: success:", data.success)
      return

    @latest_message = data

    # prase fields into javascript types
    data.original_origin = data.origin
    data.original_time = data.time
    data.origin = new Origin(data.origin)
    data.time = @parse_time(data.time)

    handler = @handlers.for(data.origin.path)
    if handler?
      handler.latest_message = data
      handler.fn(data)
    else
      if @debug?
        console.log("SQUIDWORK: info: no handler for path", data.origin.path)

  _send: (data) ->
    """
    wait for the socket to open, and then send the data
    no garuntee on ordering
    """
    if @socket.readyState != 1
      # buffer
      @_buffer.push(data)
      return

    @socket.send(data)

  _unbuffer: () =>
    for msg in @_buffer
      @socket.send(msg)

  # subscribe to the Squidwork events on URI at path
  # adding an event handler for JS callbacks.
  # Opens a new ZeroMQ socket on the server
  subscribe: (uri, path, fn) ->
    req = JSON.stringify({action: 'SUB', target: [uri, path]})
    @_send(req)
    @handlers.add(path, fn)

  # unsubscribe from events on the given socket and prefix
  # the socket will be closed on the server
  unsubscribe: (uri, path) ->
    req = JSON.stringify({action: 'UNSUB', target: [uri, path]})
    @_send(req)
    @handlers.remove(path)

###
# templating intensifies:
# we use these template values to pre-construct a squidwork instance
# with the correct websocket values
###
WEBSOCKET_URI = '{{ socket_uri }}'
DEBUG = '{{ debug }}' == 'True'
window.squidwork = new Squidwork(WEBSOCKET_URI, DEBUG)
window.SquidworkConnection = Squidwork
