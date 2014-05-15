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

class HandlerList
  constructor: () ->
    # kept sorted by length for fast filtering
    # from shortest to longest
    @handlers = []

    # easily tell if we just need to do a replace
    # maps from path --> index in @handlers
    @exactPaths = {}

  # add a handler for a path
  add: (path, fn) ->
    if @exactPaths[path]?
      @exactPaths[path].fn = fn
      return

    # the handler
    h = {path: path, fn: fn}

    # store in exact lookup path
    @exactPaths[path] = h
    # store by position
    idx = @idxForLength(path.length)
    @handlers.splice(idx, 0, h)

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

  # find the index where something on lenght `len` should be.
  idxForLength: (len) ->
    # base case: empty array
    if @handlers.length == 0
      return 0

    key = (index) => @handlers[index].path.length
    max_idx = @handlers.length - 1
    min_idx = 0

    while (min_idx < max_idx)
      mid_idx = Math.floor(max_idx - min_idx / 2)

      if key(mid_idx) < len
        min_idx = mid_idx + 1
      else
        max_idx = mid_idx
    # left to the caller to determine if @handlers[min_idx].path.length == len
    return min_idx

  # get the most specific handler for the given path
  for: (path) ->
    path = path.replace(PREFIX, '')

    idx = @idxForLength(path.length)

    while idx > -1
      cur = @handlers[idx]
      if path.indexOf(cur.path) == 0
        # match
        return cur.fn
      idx -= 1

"""
Subscribe and unsubscrite from squidwork event messages
"""
class Squidwork
  constructor: (@uri, @debug=false) ->
    @handlers = new HandlerList()
    @socket = new WebSocket(@uri)
    @socket.onmessage = @recieve_message

  parse_time: (str) ->
    [iso, psec] = str.split('.')
    return new Date(iso)

  recieve_message: (event) =>
    if @debug
      console.log("SQUIDWORK: event:", event)
      console.log("SQUIDWORK: raw data:", event.data)

    data = JSON.parse(event.data)

    if data.error?
      console.log("SQUIDWORK: error:", data.error)
      return

    if data.success?
      console.log("SQUIDWORK: success:", data.success)
      return

    # dispatch based on route
    origin = new Origin(data.origin)
    time = @parse_time(data.time)
    handler = @handlers.for(origin.path)

    data.origin = origin
    data.time = @parse_time(data.time)

    @latest_message = data

    handler(data)

  # subscribe to the Squidwork events on URI at path
  # adding an event handler for JS callbacks.
  # Opens a new ZeroMQ socket on the server
  subscribe: (uri, path, fn) ->
    req = JSON.stringify({action: 'SUB', target: [uri, path]})
    @socket.send(req)
    @handlers.add(path, fn)

  # unsubscribe from events on the given socket and prefix
  # the socket will be closed on the server
  unsubscribe: (uri, path) ->
    req = JSON.stringify({action: 'UNSUB', target: [uri, path]})
    @socket.send(req)
    @handlers.remove(path)

###
# templating intensifies:
# we use these template values to pre-construct a squidwork instance
# with the correct websocket values
###
WEBSOCKET_URI = '{{ WEBSOCKET_URI }}'
window.squidwork = new Squidwork(WEBSOCKET_URI)
window.SquidworkConnection = Squidwork
