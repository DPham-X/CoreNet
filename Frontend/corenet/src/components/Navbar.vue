<template>
  <div id="navbar">
    <nav class="navbar navbar-expand-sm bg-dark navbar-dark fixed-top">
      <div class="navbar-collapse w-100 order-1 order-md-0">
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
      </div>
      <div class="w-100 mx-auto order0"></div>
      <div class=" navbar-collapse w-100 order-3 order-md-0 ">
        <ul class="navbar-nav ml-auto justify-content-end">
          <li class="nav-item">
            Connected to: {{ host }}
          </li>
        </ul>
      </div>
    </nav>

    <div class="bottom-pad"></div>
  </div>
</template>

<script>
import { host } from '../variable.js'

export default {
  name: 'Navbar',
  data () {
    return {
      host: host
    }
  }
}
</script>

<style>
.icon-pad {
  padding-right: 10px;
}
</style>
