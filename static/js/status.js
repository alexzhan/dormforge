function submit(requesturl,name,domain,prevnum) {
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
            var new_comment_item = "<div class='comment-item'><div class='commavatar'><a href='/people/"+domain+"'><img width='50px' height='50px' src='/static/img/no_avatar.jpg?v=ebaa4'></a></div><div class='comment-item-content'><div class='comment-item-title'><a class='name' href='/people/"+domain+"'>"+name+"</a><span class='time'>刚刚   <img src='/static/img/reply.png' align='absmiddle' border='0' alt='回复 "+name+"' onclick='replyOne('"+name+"')' class='clickable'></span></div><div class='comment-item-body'><p>"+commenttext+"</p></div></div></div>";
            $(".status-comment").append(new_comment_item);
        }       
    });
    return false;
}

function getCookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
}
