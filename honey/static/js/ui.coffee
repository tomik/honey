
#
# exposed variables from the server are:
# nodes: list of raw nodes
# initPath: short path where to start in the game
# postUpdateURL: generated url for ajax updates posting
# postCommentURL: generated url for ajax comments posting
#

# ==>> COMMENTS

pathCompare = (a, b) ->
  # compares that two short paths are equivalent
  if a.length != b.length
    return false
  for i in [0...a.length]
    if a[i][0] != b[i][0] or a[i][1] != b[i][1]
      return false
  return true

class UIHandler
  constructor: (@commentPaths) ->

  # handles all the visual interaction with the user
  # namely showing / hiding buttons and showing / hiding comments
  onSynced: (game) ->
    $("#commit_btn").button("reset")
    $("#commit_btn").hide()

  onUnsynced: (game) ->
    $("#commit_btn").show()

  onChangeMode: (newMode) ->
    $("#mode_info").html("mode #{newMode}")

  onLoad: (game, node) ->
    @refreshComments(_bridge.getCurrNodeShortPath())
    @refreshCommentsStats()

  onPlayMove: (game, node) ->
    @refreshComments(_bridge.getCurrNodeShortPath())

  onUnplayMove: (game, node) ->
    @refreshComments(_bridge.getCurrNodeShortPath())

  refreshComments: (path) ->
    # Makes sure only comments for given tree path are visible. 
    currComments = (comment for comment in @commentPaths when pathCompare(comment[1], path))
    $("#comments .comment").hide()
    for comment in currComments
      elem = $("#comment_#{comment[0]}")
      elem.show()

  refreshCommentsStats: () ->
    # Updates stats in the comment game details section (number of comments, last one, etc.).
    if @commentPaths.length > 0
      $("#comments_stats").text(@commentPaths.length)
    else
      $("#comments_stats").text("No comments yet.")

  addComment: (comment_id, comment_path, commentHTML) ->
    @commentPaths.push([comment_id, comment_path])
    $("#comments").append(commentHTML)
    @refreshComments(_bridge.getCurrNodeShortPath())
    @refreshCommentsStats()

  removeComment: (comment_id) ->
    $("#comment_#{comment_id}").remove()
    for commentPath, index in @commentPaths
      if commentPath[0] == comment_id
        @commentPaths.splice(index, 1)
        break
    @refreshCommentsStats()

_uiHandler = new UIHandler(commentPaths)
@_bridge = new Bridge(nodes, initPath, _uiHandler)

sendSync = () ->
  if _bridge.isGameSynced()
    return false
  $.post(
    postUpdateURL,
    {"update_data": JSON.stringify(_bridge.getNodes())},
    (reply) ->
      if("err" of reply and reply.err)
        alert(reply["err"])
      # now the game is in sync with the server again
      _bridge.syncGame()
  )

checkFocus = () ->
  if $("#edit_game").is(":visible") or $("#post_comment").is(":visible")
    _bridge.setFocus(false)
  else
    _bridge.setFocus(true)
  # applyFocus
  if _bridge.hasFocus()
    $("#focus_toggle").addClass("active")
  else
    $("#focus_toggle").removeClass("active")

# $ init
$ ->
  # posting comments
  $("#post_comment form input[value='Post']").click(
    (e) ->
      e.preventDefault()
      sendSync()
      $("#post_comment form input[name='short_path_json']").attr("value", JSON.stringify(_bridge.getCurrNodeShortPath()))
      # send the form via ajax
      $.post(
        postCommentURL,
        $("#post_comment form").serialize(),
        (reply) ->
          if("err" of reply and reply.err)
            alert(reply["err"])
          _uiHandler.addComment(reply.comment_id, reply.comment_path, reply.comment_html)
          $("#post_comment_toggle").click()
        )
  )
  # toggling
  $("#edit_game_toggle").click(
    (e) ->
      $("#edit_game").toggle()
      checkFocus()
      e.preventDefault()
  )
  $("#focus_toggle").click(
    (e) ->
      _bridge.setFocus(not _bridge.hasFocus())
      e.preventDefault()
  )
  $("#post_comment_toggle").click(
    (e) ->
      $("#post_comment").toggle()
      checkFocus()
      e.preventDefault()
  )
  $("#commit_btn").click(
    (e) ->
      $("#commit_btn").button("loading")
      e.preventDefault()
      sendSync()
  )
  # toggle forms that have errors
  if (gameEditFormHasErrors)
    $("#edit_game_toggle").click()
  checkFocus()

