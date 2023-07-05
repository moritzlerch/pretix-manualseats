$(() => {
  const downloadSeatBtn = $("#download-seat");
  const downloadOrderPosBtn = $("#download-orderpos");

  downloadSeatBtn.on("click", () => {
    const data = document.getElementById("seat-csv").innerText;
    const filename = "event-seats.csv";
    download(data, filename);
  });

  downloadOrderPosBtn.on("click", () => {
    const data = document.getElementById("orderpositions-csv").innerText;
    const filename = "event-orderpos.csv";
    download(data, filename);
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
