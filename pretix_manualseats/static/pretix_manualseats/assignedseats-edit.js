$(() => {
    const downloadAssignedSeatsBtn = $("#download_assignedseats");
    const uploadAssignedSeatsBtn = $("#upload_assignedseats");
    const clearAssignedSeatsBtn = $("#clear_assignedseats");
    const idData = $("#id_data");

    function updateDownloadButton() {
        downloadAssignedSeatsBtn.prop("disabled", !idData.val().startsWith("seat_guid,orderposition_secret\n"));
    }

    idData.on("change", updateDownloadButton());

    uploadAssignedSeatsBtn.on("click", () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = ".csv";
        input.onchange = (e) => {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                const contents = e.target.result;
                idData.val(contents);
                updateDownloadButton();
            };
            reader.readAsText(file);
        };
        input.click();
    });

    downloadAssignedSeatsBtn.on("click", () => {
        const data = idData.val();
        const filename = "assignedseats.csv";
        download(data, filename);
    });

    clearAssignedSeatsBtn.on("click", () => {
        idData.val("");
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
