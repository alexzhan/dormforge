function submitfunc(requesturl,name,domain,prevnum) {
    var commenttext = $('#comment-box').val();
    if (commenttext == '')
        return false;
    $.ajax({
        type:'POST',
        url:requesturl,
        data:{commenttext:commenttext,_xsrf:getCookie('_xsrf')},
        success:function(data){
            $("#number").text("评论("+(parseInt(prevnum)+1)+")");
            $('#comment-box').val("");
            var replystr = "replyOne('" + name + "')";
            var new_comment_item = "<div class='comment-item'><div class='commavatar'><a href='/people/"+domain+"'><img width='50px' height='50px' src='/static/img/no_avatar.jpg?v=ebaa4'></a></div><div class='comment-item-content'><div class='comment-item-title'><a class='name' href='/people/"+domain+"'>"+name+"</a><span class='time'>刚刚   <img src='/static/img/reply.png' align='absmiddle' border='0' alt='回复 "+name+"' onclick="+replystr+" class='clickable'></span></div><div class='comment-item-body'><p>"+data+"</p></div></div></div>";
            $(".status-comment").append(new_comment_item);
        }       
    });
    return false;
}
function replyOne(username) {
    replyContent = $("#comment-box");
    oldContent = replyContent.val();
    prefix = "@" + username + " ";
    newContent = '';
        if(oldContent.length > 0){
            if (oldContent != prefix) {
                newContent = prefix + oldContent;
            }
        } else {
            newContent = prefix;
        }
    replyContent.focus();
    replyContent.val(newContent);
}
function getCookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
}
