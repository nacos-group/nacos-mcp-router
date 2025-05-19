import axios from 'axios';

const nacosAddr = 'localhost:8848';
const userName = 'nacos';
const passwd = 'nacos_password';


async function main() {
let config = {
    method: 'get',
    // maxBodyLength: Infinity,
    url: `http://${nacosAddr}/nacos/v3/admin/ai/mcp/list?pageNo=1&pageSize=100`,
    headers: { 
      'Content-Type': 'application/json', 
      'charset': 'utf-8', 
      'userName': userName, 
      'password': passwd
    }
  };

  axios.request(config)
  .then((response) => {
    console.log(JSON.stringify(response.data));
  })
  .catch((error) => {
    console.log(error);
  });
}

main();
