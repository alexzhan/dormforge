function submitdoc() {
    $("#linktitle").removeClass("error");
    $("#dochelp").text("");
    if($("#title").val().length == 0){
        $("#linktitle").removeClass();
        $("#linktitle").addClass("control-group error");
        return false;
    }
    if($("#doc").val().length == 0){
        $("#dochelp").text("请选择文件");
        return false;
    }
    if($("#doc").val().split(".").pop() in {doc:1, docx:1, ppt:1, pptx:1, xls:1, pdf:1} ) {
        $("#docbtn").addClass("disabled");
    }
    else {
        $("#dochelp").text("暂时不支持该文档格式");
        return false;
    }
}
