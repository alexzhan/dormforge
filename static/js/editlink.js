$(document).ready(function() {
    if($("#sug").text() == '0'){
        modaltoggle(0);
    }
});
function cansug() {
    if($("#sug").text() != '0')
        return true;
    $.ajax({
    type:'POST',
    url:'/cansug',
    data:{_xsrf:getCookie('_xsrf')},
    success:function(data){
        $("#sug").text("1");
    }       
    });
}
function modaltoggle(option) {
    if(option) 
        $(".suggestbox").hide();
    var ie = document.all ? 1 : 0;
    if(ie){
        $("#cr").hide();
        $("#ie").show();
    }
    else{
        $("#ie").hide();
        $("#cr").show();
    }
    $('#crModal').modal('toggle');
    return false;
}
function editlink(pubtype) {
    var linktype = 0;
    if ($("#secret").attr("checked")=="checked"){
        linktype = 1;
    }
    var linkurl = $("#url").val();
    var linktitle = $("#title").val();
    var linksummary = $("#summary").val();
    var linktag = $("#tag").val();
    var oldtag = $("#oldtag").val();
    var linkid = $("#linkid").val();
    $("#linkurl").removeClass("error");
    if(linkurl.length == 0) {
        $("#linkurl").removeClass();
        $("#linkurl").addClass("control-group error");
        return false;
    }
    $.ajax({
    type:'POST',
    url:'/link/edit',
    data:{
        linkurl:linkurl,
        linktitle:linktitle,
        linksummary:linksummary,
        linktag:linktag,
        oldtag:oldtag,
        linktype:linktype,
        pubtype:pubtype,
        linkid:linkid,
        _xsrf:getCookie('_xsrf')},
    success:function(data){
        window.location.href=pubtype==1?data:"/";
    } 
    });
    return false;
}
function cancelbtn(pubtype, url, linkid){
    if(pubtype == 1 && url != '0'){
        window.location.href=url;
        return false;
    }
    else if (pubtype == 2 && linkid != '0'){
        window.location.href="/link/" + linkid;
        return false;
    }
}
