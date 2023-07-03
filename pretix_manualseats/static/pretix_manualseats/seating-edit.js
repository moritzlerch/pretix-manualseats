$(function () {
    const layoutUpload = $("#layout_upload");
    const idLayout = $("#id_layout");
    const layoutDownload = $("#layout_download");

    function searchJson(json, key) {
        if (typeof json === 'object' || json !== null) {
            value = JSON.parse(json)[key];
            return value || null;
        }
    }

    function updateLayoutDownloadButton() {
        layoutDownload.prop("disabled", !idLayout.val());
    }

    layoutUpload.prop("disabled", idLayout.prop("disabled"));
    idLayout.on("change", updateLayoutDownloadButton);
    updateLayoutDownloadButton();

    layoutUpload.on("click", function () {
        const input = $("<input>", { type: "file", accept: ".json" });
        input.on("change", function (e) {
            const fileReader = new FileReader();
            fileReader.onload = () => {
                idLayout.val(fileReader.result);
                updateLayoutDownloadButton();
            };
            fileReader.readAsText(input[0].files[0]);
        });
        input.click();
    });

    layoutDownload.on("click", function () {
        const url = URL.createObjectURL(new Blob([idLayout.val()]));
        const name = searchJson(idLayout.val(), "name");
        const filename = name ? (name + ".json") : "seatingplan.json";
        const a = $("<a>", { style: "display: none", href: url, download: filename });
        $("body").append(a);
        a[0].click();
        URL.revokeObjectURL(url);
    });
});


