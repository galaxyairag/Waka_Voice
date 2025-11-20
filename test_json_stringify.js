// Test pour voir comment JSON.stringify gère les propriétés undefined

console.log("="*70);
console.log("Test JSON.stringify avec propriétés undefined");
console.log("="*70);

// Cas 1: propriété existe avec valeur undefined
const obj1 = {
    character: 'farhan',
    style: undefined,
    background: '#FFFFFF'
};

console.log("\n1. Objet avec style: undefined");
console.log("   Object:", obj1);
console.log("   'style' in obj1:", 'style' in obj1);
console.log("   JSON.stringify:", JSON.stringify(obj1));

// Cas 2: propriété n'existe pas du tout
const obj2 = {
    character: 'farhan',
    background: '#FFFFFF'
};

console.log("\n2. Objet sans propriété style");
console.log("   Object:", obj2);
console.log("   'style' in obj2:", 'style' in obj2);
console.log("   JSON.stringify:", JSON.stringify(obj2));

// Cas 3: accès à propriété inexistante
const obj3 = {
    character: 'farhan',
    background: '#FFFFFF'
};

const avatarStyle = obj3.style; // undefined

console.log("\n3. Propriété accédée mais non définie");
console.log("   avatarStyle:", avatarStyle);
console.log("   'style' in obj3:", 'style' in obj3);

// Si on ajoute conditionellement avec undefined
if (avatarStyle) {
    obj3.style = avatarStyle;
    console.log("   Style ajouté (ne devrait pas arriver)");
} else {
    console.log("   Style NON ajouté (correct)");
}

console.log("   'style' in obj3 after:", 'style' in obj3);
console.log("   JSON.stringify:", JSON.stringify(obj3));

console.log("\n" + "="*70);
