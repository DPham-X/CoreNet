<template>
  <div class="body">
    <h1>{{ msg }}</h1>
    <input name="search">
    <button v-on:click="performSearch">Search</button>
    <div class="bottom-pad"></div>
    <div>
      <b-container fluid>
        <b-table
          striped
          hover
          dark
          small
          bordered
          show-empty
          :items="events"
          :fields="fields"
          :current-page="currentPage"
          :per-page="perPage"
        >
          <span slot="binded_events" slot-scope="data" v-html="data.value"/>
          <span slot="commands" slot-scope="data">
            <template v-for="(command, i) in data.item.commands">
              <tr :key="command + i">
                <td align="left" class="font-weight-bold" style="padding: 0; height:100%; width:100%">{{toUpper(command.type)}} -> {{ command.cmd }} </td>
                <td align="right">
                  <b-button size="sm" v-b-modal.cmdModal @click="sendCommands(command)"> Output </b-button>
                </td>
              </tr>
            </template>
          </span>
        </b-table>

        <b-modal id="cmdModal" title="Executed command output" size="xl" class="font-black" scrollable=true style="overflow-x:auto; max-width: 100vh">
          <div class="font-monospace" v-html="commandOutput"></div>
        </b-modal>

        <div class="mt-3 text-center">
          <b-pagination
            :total-rows="totalRows"
            :per-page="perPage"
            v-model="currentPage"
            class="my-0"
            align="center"
          />
        </div>
      </b-container>

    </div>
  </div>
</template>

<script>
import axios from 'axios'
import yaml from 'js-yaml'

export default {
  name: 'Executions',
  data () {
    return {
      commandOutput: '',
      commandArgs: '',
      msg: 'Executions',
      fields: [
        {
          key: 'name',
          label: 'Execution Name',
          sortable: true
        },
        {
          key: 'binded_events',
          label: 'Watched Events',
          formatter: 'toString'
        },
        {
          key: 'commands',
          label: 'Executed Commands',
          formatter: 'toString2'
        },
        {
          key: 'status',
          label: 'Status',
          sortable: true
        },
        {
          key: 'time',
          label: 'Date',
          formatter: 'convertIsoDate',
          sortable: true
        },
        {
          key: 'uuid',
          label: 'UUID',
          sortable: true
        }
      ],
      events: this.performSearch(),
      totalRows: 5,
      perPage: 5,
      currentPage: 1
    }
  },
  created () {
    this.performSearch()
  },
  methods: {
    performSearch: function () {
      const link = 'http://10.49.227.135:5000/'
      const apiLink = link + 'executions'

      axios
        .get(apiLink)
        .then(response => {
          this.events = response.data
          this.totalRows = this.events.length
        })
        .catch(error => {
          console.log(error)
        })
    },
    getEvents: function () {
      setInterval(this.performSearch, 1000)
    },
    convertIsoDate: function (isodate) {
      let date = new Date(isodate)
      let year = date.getFullYear()
      let month = date.getMonth() + 1
      let dt = date.getDate()
      let hour = date.getHours()
      let minutes = date.getMinutes()
      let seconds = date.getSeconds()

      if (dt < 10) {
        dt = '0' + dt
      }
      if (month < 10) {
        month = '0' + month
      }
      if (hour < 10) {
        hour = '0' + hour
      }
      if (minutes < 10) {
        minutes = '0' + minutes
      }
      if (seconds < 10) {
        seconds = '0' + seconds
      }

      let output = dt + '-' + month + '-' + year + ' ' + hour + ':' + minutes + ':' + seconds
      return output
    },
    toUpper: function (string) {
      return string.toUpperCase()
    },
    toTitle: function (string) {
      let str = string.toLowerCase()
      str = str.split(' ')

      for (var i = 0; i < str.length; i++) {
        str[i] = str[i].charAt(0).toUpperCase() + str[i].slice(1)
      }

      return str.join(' ')
    },
    toString: function (string) {
      let jsonConverted = JSON.parse(JSON.stringify(string))
      let yamlConverted = yaml.dump(jsonConverted)
      let htmlConverted = this.convertBreak(yamlConverted)
      return htmlConverted
    },
    convertBreak: function (str) {
      if (!str) {
        return '' // don't want `undefined` printing into page
      }
      // if it's something other than string, return it as is
      if (typeof str === 'string') {
        return '<div class="text-left">' + str.replace(/\n/g, '<br>').replace(/\s/g, '&nbsp') + '</div>'
      } else {
        return str
      }
    },
    removeOutput: function (jsonObject) {
      for (var i = 0; i < jsonObject.length; i++) {
        let type = jsonObject[i]

      if ('output' in jsonObject[i][type]) {
            delete jsonObject[i][type]['output']
        }
      }
      return jsonObject
    },
    sendCommands: function (command) {
      this.commandOutput = this.convertBreak(command.output)
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.details {
  color: #000000;
}
.bottom-pad {
  margin-bottom: 10px;
}
.font-monospace {
  font-family: Consolas, monospace, "Courier New";
}
.font-black {
  color: #000000;
}
</style>
.modal-header .ok .cancel {
  display: none;
}
