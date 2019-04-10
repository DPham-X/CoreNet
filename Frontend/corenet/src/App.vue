<template>
  <div id="app" class="bg">
    <app-navbar></app-navbar>
    <div class="pad"></div>
    <router-view/>
  </div>
</template>

<script>
import Navbar from './components/Navbar'

export default {
  name: 'App',
  components: {
    'app-navbar': Navbar
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #ffffff;
  margin-top: 55px;
  display: block;
  float: center;
  background-color: #2d2d2d;
}
.pad {
  height: 20px;
}
</style>
