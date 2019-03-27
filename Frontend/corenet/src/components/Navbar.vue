<template>
  <div id="navbar">
    <nav class="navbar navbar-expand-sm bg-dark navbar-dark fixed-top">
      <!-- Links -->
      <ul class="navbar-nav">
        <li class="nav-item">
          <img src="../assets/logo.png" height="40" class="icon-pad">
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#/home">Home</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#/events">Events</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#/executions">Executions</a>
        </li>
      </ul>
    </nav>
    <div class="bottom-pad"></div>
  </div>
</template>

<script>
export default {
  name: 'Navbar'
}
</script>

<style>
.icon-pad {
  padding-right: 10px;
}
</style>
