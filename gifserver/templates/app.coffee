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
  """
  <figure class="hover-card" style="top: #{top}px; left: #{60}px">
    <img src="#{row.image_uri}">
    <figcaption>
      #{escape_html(row.name)}
    </figcaption>
  </figure>
  """


$(document).ready () ->
  for el in $('tr.file')
    row = Row.from_dom(el)
    icon = $(el).find('td.thumb')
    icon.on('mouseenter', row.mouse_enter)
    icon.on('mouseleave', row.mouse_leave)
