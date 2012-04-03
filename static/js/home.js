$(document).ready(function() {
    var ie = document.all ? 1 : 0;
    if(ie){
        $("#pubtextarea").val("你在想什么?");
        $("#pubtextarea").css("color","#A9A9A9");
    }
    if($("#hn20").text() == "0") {
        $("#morebtn").hide();
    }
});

$('#pubtextarea').focus(function() {
    var ie = document.all ? 1 : 0
    if(ie) 
        if($("#pubtextarea").val()=="你在想什么?")
            $("#pubtextarea").val("");
    $("#pubtextarea").css("height","60");
    $("#pubtextarea").css("color","#333");
    $(".submit-btn").show();
}).blur(function() {
    var ie = document.all ? 1 : 0
    if($("#pubtextarea").val() == ""){
        $('.submit-btn').hide();
        $('#pubtextarea').css('height','18');
    }
    if(ie) 
        if($("#pubtextarea").val()==""){
            $("#pubtextarea").val("你在想什么?");
            $("#pubtextarea").css("color","#A9A9A9");
        }
});

function submit(name, domain) {
    var statustext = $('#pubtextarea').val();
    if (statustext == '')
        return false;
    $.ajax({
    type:'POST',
    url:'/pubstatus',
    data:{statustext:statustext,_xsrf:getCookie('_xsrf')},
    success:function(data){
        statusavatar = data.split(",", 2);
        pstatusid = statusavatar[0];
        pavatar = statusavatar[1];
        pstatus = data.substr(pstatusid.length + pavatar.length + 2);
        $('.feed-body').prepend("<div class='feed-item'><div class='avatar'><a href='/people/"+domain+"'><img width='50px' height='50px' src="+pavatar+"></a></div><div class='feed-item-content'><div class='feed-item-title'><a class='feed-item-title name' href='/people/"+domain+"'>"+name+"</a> <span class='feed-item-title desc'>更新了状态:</span></div><div class='feed-item-body'><p>"+pstatus+"</p></div><div class='feed-item-footer'><div style='float:left'><span><a class='footerlink' href='/status/"+pstatusid+"'>刚刚</a></span></div><div style='float:right'><span><a class='footerlink' href='/status/"+pstatusid+"'>评论</a></span></div></div></div></div>");
        if ($(".noinfo").length>0) {
            $(".noinfo").hide();
        }
        $('.submit-btn').hide();
        $('#pubtextarea').val('');
        $('#pubtextarea').css('height','18');
    }       
    });
}

function deleteactivity(item_id, user, actid, acttype){
    $.ajax({
    type:'POST',
    url:'/deleteactivity',
    data:{user:user,actto:actid,acttype:acttype,_xsrf:getCookie('_xsrf')},
    success:function(data){
        $("#feed-item" + item_id).hide('slow');
    }       
    });
    return false;
}
function viewnote(note_id, note_index) {
    if($("#allnote"+note_index).text() != ""){
        $("#note"+note_index).hide();
        $("#allnote"+note_index).show();
        return false;
    }
    $.ajax({
    type:'POST',
    url:'/viewnote',
    data:{note_id:note_id,_xsrf:getCookie('_xsrf')},
    success:function(data){
        if(data != "wrong"){
            data = data + "<a href='#' onclick='return togglenote(" + note_index + ")'>« 收起</a>";
            $("#note"+note_index).hide();
            $("#allnote"+note_index).html(data);
        }
    }       
    });
    return false;
}
function togglenote(note_index){
    $("#allnote"+note_index).hide();
    $("#note"+note_index).show();
    return false;
}
function morefeed(prop) {
    var lastindex = $("#li").text();
    $("#morebtn").text("加载中...");
    $.ajax({
    type:'GET',
    url:'/more/' + prop,
    data:{lastindex:lastindex,_xsrf:getCookie('_xsrf')},
    success:function(data){
        $(".feed-body").append(data);
        $("#li").text(parseInt(lastindex) + 20);
        var hnid = "#hn"+(parseInt(lastindex) + 20);
        if($(hnid).text() == "1"){
            $("#morebtn").text("更多");
        }
        else {
            $("#morebtn").hide();
        }
    }       
    });
    return false;
}
