function showbtn() {
    $("#pubtextarea").css("height","60");
    $(".submit-btn").show();
}

function hidebtn() {
    if($("#pubtextarea").val() == ""){
        $('.submit-btn').hide();
        $('#pubtextarea').css('height','18');
    }
    return false;
}

function submit() {
    var statustext = $('#pubtextarea').val();
    if (statustext == '')
        return false;
    $.ajax({
    type:'POST',
    url:'/pubstatus',
    data:{statustext:statustext,_xsrf:getCookie('_xsrf')},
    success:function(data){
        $('.feed-body').prepend("<div class='feed-item'><div class='avatar'><a href='#'><img width='50px' height='50px' src='../static/img/no_avatar.jpg'></a></div><div class='feed-item-content'><div class='feed-item-title'><a class='feed-item-title name' href='/people/alex'>alex</a> <span class='feed-item-title desc'>更新了状态:</span></div><div class='feed-item-body'><p>"+statustext+"</p></div><div class='feed-item-footer'><span><a class='footerlink' href='#'><i class='icon-retweet'></i>推荐0</a></span> <span class='splitter'>•</span> <span><a class='footerlink' href='#'><i class='icon-comment'></i>评论0</a></span> <span class='splitter'>•</span> <span><a class='footerlink' href='#'><i class='icon-time'></i>刚刚</a></span></div></div></div>");
        $('.submit-btn').hide();
        $('#pubtextarea').val('');
        $('#pubtextarea').css('height','18');
    }       
    });
}

function deletestatus(item_id, user, status_id){
    $.ajax({
    type:'POST',
    url:'/deletestatus',
    data:{user:user,actto:status_id,_xsrf:getCookie('_xsrf')},
    success:function(data){
        $("#feed-item" + item_id).hide('slow');
    }       
    });
}

function getCookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
}
