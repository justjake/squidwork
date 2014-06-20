"""
wee
"""

# explicit imports
squidwork = window.squidwork
m = window.Mithril

###############################################################################
#                                  VIEWS                                      #
###############################################################################

AppView = (ctrl) ->
  window.controller = ctrl
  m 'html', [
    m('head', [
      m('title', 'yes, my liege?'),
      m('link[rel=stylesheet][href=/style.css]')
    ]),
    m 'body', [
      m('form.commander', {onsubmit: ctrl.submit}, [
        m('input[type=text][placeholder=yes, my liege?][autofocus]', {
          value: ctrl.query(),
          onchange: m.withAttr('value', ctrl.query)
        })
      ]),
      MessageList(ctrl.messages())
    ]
  ]

MessageList = (msgs) ->
  m 'section.messages', [
    m 'ol.message-list', msgs.map (msg) ->
      m 'li.message', {class: msg.origin.toString()}, [
        m('.info', [
          m('span.origin', msg.origin.toString()),
          m('span.time', msg.time.toString())
        ]),
        m '.data', render_json(msg.content)
      ]
  ]

render_json = (data) ->
  # adapted from http://stackoverflow.com/questions/4810841/how-can-i-pretty-print-json-using-javascript
  # wraps JSON data in span elements so that syntax highlighting may be
  # applied. Should be placed in a `whitespace: pre` context
  if typeof(data) isnt 'string'
    data = JSON.stringify(data, undefined, 2)

  # these regexes are ORed together to form the JSON tokenizer
  unicode =     /"(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?/
  keyword =     /\b(true|false|null)\b/
  whitespace =  /\s+/
  punctuation = /[,.}{\[\]]/
  number =      /-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/

  # combine by | or-ing
  syntax = '(' + [unicode, keyword, whitespace,
            punctuation, number].map((r) -> r.source).join('|') + ')'
  parser = new RegExp(syntax, 'g')

  nodes = data.match(parser) ? []
  select_class = (node) ->
    if punctuation.test(node)
      return 'punctuation'
    if /^\s+$/.test(node)
      return 'whitespace'
    if /^"/.test(node)
      if /:$/.test(node)
        return 'key'
      return 'string'

    if /true|false/.test(node)
      return 'boolean'

     if /null/.test(node)
       return 'null'
     return 'number'
  return nodes.map (node) ->
    cls = select_class(node)
    return m('span', {class: cls}, node)


###############################################################################
#                                  MODELS                                     #
###############################################################################

class MessageCache
  """
  keep a cache of the @max_count last messages, as well as a map of the latest
  message from each origin
  """
  constructor: (@max_count, latest=[], by_origin={}) ->
    @cache = []
    @callbacks = []
    @by_origin = {}
    @insert(latest...)
    # explicity set by_origin after add so we have the correct
    # initial state
    @by_origin = by_origin

  insert: (messages...) ->
    for msg in messages
      @by_origin[msg.origin] = msg

    @cache = @cache.concat(messages)[-@max_count..]


###############################################################################
#                                CONTROLLERS                                  #
###############################################################################

class Set
  constructor: (items...) ->
    @hashset = {}
    @add(items...)

  add: (items...) ->
    for i in items
      @hashset[i] = true
    this

  items: () ->
    items = []
    for i of @hashset
      items.push(i)
    items

class LiegeController
  """
  submits dingus to get wit response
  on window creation, listens to all wit messages
  """
  constructor: () ->
    @cache = new MessageCache(20)
    @query = m.prop('')
    uris = new Set()
    for route of squidwork.services
      uris.add(squidwork.services[route]...)
    for uri in uris.items()
      console.log 'subscribing', uri
      squidwork.subscribe(uri, 'wit', @recieve_message)

  messages: () ->
    @cache.cache.sort((a, b) -> b.time - a.time)

  recieve_message: (msg) =>
    @cache.insert(msg)
    m.redraw()

  submit: (e) =>
    e.preventDefault()
    m.request(method: 'GET', url: '/wit', data: {q: @query()})
    @query('')

###############################################################################
#                               ENTRY POINT                                   #
###############################################################################

app = window.app = {}
app.MessageCache = MessageCache
app.LiegeController = LiegeController
app.AppView = AppView

Mithril.module(document, {view: AppView, controller: LiegeController})
