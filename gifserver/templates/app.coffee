class Row
  constructor: (@name, @image_uri, @hits, @modified) ->

  # dom-based constructor
  @from_dom = (dom_el) ->
    $el = $(dom_el)
    image_uri = $el.find('a').attr('href') + '?count=false' # don't count for
    hits = parseInt($el.find('td.hits').text(), 10)
    name = $el.find('td.name').text() or ""
    modified = $el.find('td.modified').text()
    row = new Row(name, image_uri, hits, modified)
    row.dom = $el[0]
    return row

  # creates an image dom element
  load_image: () ->
    if @image?
      return @image

    @image = new Image()
    @image.src = @image_uri
    return @image

  mouse_enter: (evt) =>
    # already queued view
    if (@popup_timeout)
      return
    @load_image()
    @popup_timeout = setTimeout(@show_popup, 50)

  mouse_leave: (evt) =>
    if @popup_timeout
      clearTimeout(@popup_timeout)
      @popup_timeout = null
    @hide_popup()

  # not the most graceful way to do this, but im not doing an app's worth
  # of engineerign to show a lightbox
  show_popup: () =>
    view = HoverCardView(this)
    $popup = $('#popup')
    #m.render($popup[0], [view])
    $popup[0].innerHTML = view
    $popup.show()

    # keep image from folling off page
    $fig = $popup.find('.hover-card')
    {top, left} = $fig.offset()
    bottom_of_el = top + $fig.outerHeight() + 20
    bottom_of_page = $(window).scrollTop() + $(window).height()
    offset = bottom_of_page - bottom_of_el
    if offset < 0
      # we were off the page to some extent
      # reposition by offset
      $fig.offset(top: top + offset, left: left)
    
    
    # sharpen-ify: replace with little version
    # so you can right-click -> copy link location (??)
    # $(@dom).find('img.thumb').attr('src', @image_uri)
    # maybe in the future :)

  hide_popup: () =>
    $('#popup').hide()


window.escape_html = escape_html = (str) ->
   div = document.createElement('div')
   div.appendChild(document.createTextNode(str))
   return div.innerHTML

HoverCardView = (row) ->
  {top, left} = $(row.dom).offset()
  top += $(row.dom).height()
  name = row.name
  [title..., extension] = name.split('.')
  title = title.join(' ').replace(/_|-/g, ' ')
  """
  <figure class="hover-card" style="top: #{top}px; left: #{60}px">
    <img src="#{row.image_uri}">
    <figcaption>
      #{escape_html(title)}
    </figcaption>
  </figure>
  """

# the DragController oversees HTML5 drag-and-drop uploading of images,
# or of remote downloading of URLs to images
# @see https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Drag_and_drop#events
class UploadController

  constructor: () ->
    @view = $('#drag-target')
    span = @view.find('span')
    @view_text = (txt) -> span.text(txt)
    console.log('got view', @view)

  every: (evt) =>
    @latest_event = evt
    @data_transfer = evt.dataTransfer

  # mouse first moves over controller while dragging
  drag_enter: (evt) =>
    if @abort_drag_timeout
      clearTimeout(@abort_drag_timeout)
      @abort_drag_timeout = null

    @every(evt)
    console.log "Drag enter", evt
    evt.preventDefault()

    @view_text('welcome to drag')
    @view.show()
    
    # assume we lost interest after a while
    @abort_drag_timeout = setTimeout((-> @drag_leave(evt)).bind(this), 1000)

    return false


  # fired while mouse moves
  drag_over: (evt) =>
    @every(evt)
    #console.log "Drag over", evt
    # allow drops
    evt.preventDefault()
    return false

  drag_leave: (evt) =>
    @every(evt)
    console.log "Drag leave", evt
    # hide targeting overlay
    @view.hide()

  drag_end: (evt) =>
    @every(evt)
    console.log "Drag end", evt
    @drag_leave(evt)

  drop: (evt) =>
    @every(evt)
    console.log "Drop!", evt
    evt.preventDefault()  # don't navigate or whatever

    item = window.ITEM = evt.dataTransfer.items[0]
    console.log('GOT ITEM', item)

    console.log('otherwise DT = ', evt.dataTransfer)
    debug_cb = (msg = 'cb revealed') ->
      (things...) -> console.log(msg, things...)

    if item.type[0..5] == 'image/'
      item.getAsString(debug_cb('as string'))
      item.getAsFile(debug_cb('as file'))
      console.log('perform upload here')
    else if item.type is 'text/uri-list'
      item.getAsString(debug_cb('as string'))
      console.log('perform download here')
      return
    else
      alert("Don't know nothin' bout #{item.type} dropper-doos, no sir!")

    @drag_end(evt)


$(document).ready () ->

  # we accept any dragging into the body
  window.uc = uc = new UploadController()
  # $('body').on('dragstart', uc.drag_start)
  $('body').on('dragenter', uc.drag_enter)
  $('body').on('dragover', uc.drag_over)
  $('body').on('drop', uc.drop)
  #$('body').on('dragleave', uc.drag_leave)
  console.log($('body'), 'is ready')

  for el in $('tr.file')
    row = Row.from_dom(el)
    icon = $(el).find('td.thumb')
    icon.on('mouseenter', row.mouse_enter)
    icon.on('mouseleave', row.mouse_leave)
