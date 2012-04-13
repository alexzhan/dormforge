function morefeed(prop, name) {
    var lastindex = $("#li").text();
    $("#morebtn").text("加载中...");
    $.ajax({
        type:'GET',
        url:'/more/' + prop,
        data:{lastindex:lastindex,name:name},
        success:function(data){
            $(".peoplelist").append(data);
            $("#li").text(parseInt(lastindex) + 10);
            var hnid = "#hn"+(parseInt(lastindex) + 10);
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
