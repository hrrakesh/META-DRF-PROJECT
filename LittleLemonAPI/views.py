from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer
from .permissions import IsManager, IsDeliveryCrew
from datetime import date



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]



class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filterset_fields = ['category', 'price', 'featured']
    search_fields = ['title']
    ordering_fields = ['price', 'title']


    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsManager()]
        return [AllowAny()]
    

class ManagerGroupView(generics.ListCreateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]


    def get(self, request):
        managers = User.objects.filter(groups__name='Manager')
        return Response({'managers':[u.username for u in managers]})


    def post(self, request):
        user = get_object_or_404(User, id=request.data['user_id'])
        group = Group.objects.get(name='Manager')
        group.user_set.add(user)
        return Response(status=status.HTTP_201_CREATED)


    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.get(name='Manager')
        group.user_set.remove(user)
        return Response(status=status.HTTP_200_OK)


class DeliveryCrewGroupView(ManagerGroupView):
    def get(self, request):
        crew = User.objects.filter(groups__name='Delivery crew')
        return Response({'delivery_crew':[u.username for u in crew]})


    def post(self, request):
        user = get_object_or_404(User, id=request.data['user_id'])
        group = Group.objects.get(name='Delivery crew')
        group.user_set.add(user)
        return Response(status=status.HTTP_201_CREATED)
    

class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


    def perform_create(self, serializer):
        menuitem = get_object_or_404(MenuItem, id=self.request.data['menuitem_id'])
        qty = self.request.data['quantity']
        price = menuitem.price * int(qty)
        serializer.save(user=self.request.user, unit_price=menuitem.price, price=price)


    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_200_OK)



class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        if user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)


    def perform_create(self, serializer):
        user = self.request.user

        cart_items = Cart.objects.filter(user=user)
        total = sum(item.price for item in cart_items)
        order = serializer.save(user=user, total=total, date=date.today())

        for item in cart_items:
            OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity, unit_price=item.unit_price, price=item.price)
        cart_items.delete()


    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user

        if user.groups.filter(name='Manager').exists():
            if 'delivery_crew' in request.data:
                 order.delivery_crew = get_object_or_404(User, id=request.data['delivery_crew'])
            if 'status' in request.data:
                order.status = request.data['status']
            order.save()
            return Response(OrderSerializer(order).data)
            
        elif user.groups.filter(name='Delivery crew').exists():
            order.status = request.data.get('status', order.status)
            order.save()
            return Response(OrderSerializer(order).data)
        
        return Response(status=status.HTTP_403_FORBIDDEN)
    
