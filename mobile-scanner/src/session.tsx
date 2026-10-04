import React, {createContext, useContext, useEffect, useState, useCallback} from 'react';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
export type Item={product_id:string;name:string;category:string;size:string;stock:number;price?:number;qty:number};
export type Bill={id:string;number:string;total:number;method:string;created:string;items:Item[]};
type Login={token:string;user:{id:string;name:string;role:string};capabilities:string[]};
export type Pending={mode:'receive'|'sale';body:{request_id:string;items:{product_id:string;size:string;qty:number}[];method?:string;expected_total?:number}};
export class ApiError extends Error {constructor(message:string,public status:number){super(message)}}
async function call(base:string,path:string,token?:string,body?:unknown){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),25000);try{const r=await fetch(base+'/api/staff/'+path,{method:body===undefined?'GET':'POST',headers:{...(token?{Authorization:'Bearer '+token}:{}),...(body!==undefined?{'Content-Type':'application/json'}:{})},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});const d=await r.json().catch(()=>({error:'Server returned an unreadable response.'}));if(!r.ok)throw new ApiError(d.error||'Request failed',r.status);return d}finally{clearTimeout(timer)}}
type State={ready:boolean;base:string;login:Login|null;pending:Pending|null;signin:(base:string,username:string,password:string)=>Promise<void>;signout:()=>Promise<void>;api:(path:string,body?:unknown)=>Promise<any>;remember:(value:Pending|null)=>Promise<void>};
const Context=createContext<State|null>(null);
export function SessionProvider({children}:{children:React.ReactNode}){const [ready,setReady]=useState(false),[base,setBase]=useState(''),[login,setLogin]=useState<Login|null>(null),[pending,setPending]=useState<Pending|null>(null);
const key=(b:string,id:string)=>'tiny-pending:'+b+':'+id;
const restorePending=useCallback(async(b:string,id:string)=>{const raw=await AsyncStorage.getItem('tiny-pending:'+b+':'+id);setPending(raw?JSON.parse(raw):null)},[])
useEffect(()=>{(async()=>{try{const raw=await SecureStore.getItemAsync('tiny-staff-session');if(raw){const saved=JSON.parse(raw);const current=await call(saved.base,'session',saved.token);setBase(saved.base);setLogin({token:saved.token,...current});await restorePending(saved.base,current.user.id)}}catch{/* Sign-in screen appears; unresolved operations remain saved for the same staff account. */}finally{setReady(true)}})()},[restorePending]);
async function signin(url:string,username:string,password:string){const b=url.trim().replace(/\/$/,'');const u=new URL(b);if(u.protocol!=='https:'||u.username||u.password||u.pathname!=='/'||u.search||u.hash)throw new Error('Enter the HTTPS admin service origin, e.g. https://tiny-tale-admin.onrender.com');const d=await call(b,'login',undefined,{username:username.trim(),password});await SecureStore.setItemAsync('tiny-staff-session',JSON.stringify({base:b,token:d.token}));setBase(b);setLogin(d);await restorePending(b,d.user.id)}
async function signout(){if(login)await call(base,'logout',login.token,{}).catch(()=>{});await SecureStore.deleteItemAsync('tiny-staff-session');setLogin(null);setPending(null)}
async function remember(value:Pending|null){if(!login)throw new Error('Please sign in');if(value)await AsyncStorage.setItem(key(base,login.user.id),JSON.stringify(value));else await AsyncStorage.removeItem(key(base,login.user.id));setPending(value)}
const api=useCallback((path:string,body?:unknown)=>{if(!login)return Promise.reject(new Error('Please sign in'));return call(base,path,login.token,body)},[base,login]);
return <Context.Provider value={{ready,base,login,pending,signin,signout,remember,api}}>{children}</Context.Provider>}
export function useSession(){const s=useContext(Context);if(!s)throw new Error('Session context missing');return s}
