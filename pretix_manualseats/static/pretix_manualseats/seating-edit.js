$(() => {
    const uploadLayoutBtn = $("#upload_layout");
    const downloadLayoutBtn = $("#download_layout");
    const idLayout = $("#id_layout");

    function searchJson(json, key) {
        if (typeof json === 'object' || json !== null) {
            value = JSON.parse(json)[key];
            return value || null;
        }
    }

    function updateDownloadButton() {
        downloadLayoutBtn.prop("disabled", !idLayout.val());
    }

    idLayout.on("change", updateDownloadButton());

    uploadLayoutBtn.on("click", () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".json";
        input.onchange = (e) => {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                const contents = e.target.result;
                idLayout.val(contents);
                updateDownloadButton();
            };
            reader.readAsText(file);
        };
        input.click();
    });

    downloadLayoutBtn.on("click", () => {
        const data = idLayout.val();
        const name = searchJson(idLayout.val(), "name");
        const filename = name ? (name + ".json") : "seatingplan.json";
        download(data, filename);
    });

    clearAssignedSeatsBtn.on("click", () => {
        idLayout.val("");
        updateDownloadButton();
    });
});

const download = (data, filename) => {
    const url = URL.createObjectURL(new Blob([data], { type: "text/csv" }));
    const aref = document.createElement("a");
    aref.hidden = true;
    aref.href = url;
    aref.download = filename;
    document.body.appendChild(aref);
    aref.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(aref);
};
